from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_
from typing import List, Optional
from decimal import Decimal
import uuid

from app.models import Supplier, Product, SaleItem, Payout
from app.models.product_model import ProductTypeEnum, ProductStatusEnum
from app.schemas.payout_schema import PayoutCreate, SupplierPayoutSummary, PayoutSummaryItem
from app.services import supplier_service
from fastapi import HTTPException, status

def _generate_payout_number(db: Session) -> str:
    """Generates a unique payout number."""
    while True:
        payout_number = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        if not db.query(Payout).filter(Payout.payout_number == payout_number).first():
            return payout_number

def get_payout_summary_for_supplier(db: Session, supplier_id: int, limit_preview: int = 5) -> SupplierPayoutSummary:
    supplier = supplier_service.get_supplier(db, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    # Find SaleItems for this supplier that are:
    # 1. From COMMISSION products
    # 2. Product status is SOLD
    # 3. SaleItem has not yet been part of any payout (payout_id IS NULL)
    # 4. SaleItem has a commission_amount_at_sale > 0
    query = db.query(
        SaleItem.id,
        SaleItem.commission_amount_at_sale,
        Product.id.label("product_id"),
        Product.sku.label("product_sku"),
        Product.name.label("product_name"),
        SaleItem.sale_id,
        # Sale.transaction_number, # Need to join Sale for this
        # Sale.transaction_time,   # Need to join Sale for this
    ).join(Product, SaleItem.product_id == Product.id)\
     .filter(Product.supplier_id == supplier_id)\
     .filter(Product.product_type == ProductTypeEnum.COMMISSION)\
     .filter(SaleItem.payout_id.is_(None))\
     .filter(SaleItem.commission_amount_at_sale > 0)\
     .filter(Product.status == ProductStatusEnum.SOLD) # Ensure product is still considered sold

    # To get sale details, we need to join Sale table
    query_with_sale_details = query.join(SaleItem.sale)\
                                   .add_columns(Sale.transaction_number, Sale.transaction_time)


    eligible_items_for_sum = query.all() # For sum, we don't need sale details yet.
    total_due = sum(item.commission_amount_at_sale for item in eligible_items_for_sum)

    eligible_items_for_preview = query_with_sale_details.limit(limit_preview).all()

    items_preview_list = [
        PayoutSummaryItem(
            product_id=item.product_id,
            product_sku=item.product_sku,
            product_name=item.product_name,
            sale_id=item.sale_id,
            sale_transaction_number=item.transaction_number, # from joined Sale
            sale_date=item.transaction_time, # from joined Sale
            commission_amount=item.commission_amount_at_sale
        ) for item in eligible_items_for_preview
    ]

    supplier_name = supplier.company_name if supplier.company_name else f"{supplier.first_name} {supplier.last_name}"

    return SupplierPayoutSummary(
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        total_due=total_due,
        eligible_items_count=len(eligible_items_for_sum), # Count of all eligible items
        items_preview=items_preview_list
    )

def create_payout_for_supplier(db: Session, payout_in: PayoutCreate) -> Payout:
    supplier = supplier_service.get_supplier(db, supplier_id=payout_in.supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    # Get all eligible SaleItems for this supplier
    eligible_sale_items = db.query(SaleItem)\
        .join(Product, SaleItem.product_id == Product.id)\
        .filter(Product.supplier_id == payout_in.supplier_id)\
        .filter(Product.product_type == ProductTypeEnum.COMMISSION)\
        .filter(SaleItem.payout_id.is_(None))\
        .filter(SaleItem.commission_amount_at_sale > 0)\
        .filter(Product.status == ProductStatusEnum.SOLD)\
        .all()

    if not eligible_sale_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No eligible items found for payout for this supplier.")

    total_payout_amount = sum(item.commission_amount_at_sale for item in eligible_sale_items)

    if total_payout_amount <= 0:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total payout amount is zero or less, nothing to pay out.")

    payout_number = _generate_payout_number(db)
    db_payout = Payout(
        payout_number=payout_number,
        supplier_id=payout_in.supplier_id,
        payout_date=payout_in.payout_date if payout_in.payout_date else func.current_date(),
        total_amount=total_payout_amount,
        notes=payout_in.notes
    )

    db.add(db_payout)
    # We need the payout_id, so flush to get it before assigning to sale_items
    try:
        db.flush() # Get db_payout.id
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during payout creation flush: {str(e)}")


    for item in eligible_sale_items:
        item.payout_id = db_payout.id
        db.add(item)

    try:
        db.commit()
        db.refresh(db_payout)
        # Eager load supplier and items for the response
        return db.query(Payout).options(
            joinedload(Payout.supplier),
            selectinload(Payout.items_paid_out).joinedload(SaleItem.product) # Use selectinload for list relationships
        ).filter(Payout.id == db_payout.id).first()
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not complete payout transaction: {str(e)}")


def get_payout(db: Session, payout_id: int) -> Optional[Payout]:
    return db.query(Payout).options(
        joinedload(Payout.supplier),
        selectinload(Payout.items_paid_out).joinedload(SaleItem.product).joinedload(Product.category), # Example of deeper load
        selectinload(Payout.items_paid_out).joinedload(SaleItem.sale)
    ).filter(Payout.id == payout_id).first()

def get_payouts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = None
) -> List[Payout]:
    query = db.query(Payout).options(joinedload(Payout.supplier)) # Basic info for list
    if supplier_id is not None:
        query = query.filter(Payout.supplier_id == supplier_id)

    return query.order_by(Payout.payout_date.desc(), Payout.created_at.desc()).offset(skip).limit(limit).all()
