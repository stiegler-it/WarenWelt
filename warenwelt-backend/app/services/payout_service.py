from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_
from typing import List, Optional
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_
from typing import List, Optional
from decimal import Decimal
import uuid

from app.models.supplier_model import Supplier # Explicit import
from app.models.product_model import Product, ProductTypeEnum, ProductStatusEnum
from app.models.sale_model import SaleItem, Sale # Sale needed for item preview
from app.models.payout_model import Payout
from app.schemas.payout_schema import PayoutCreate, SupplierPayoutSummary, PayoutSummaryItem
from app.services import supplier_service # To get supplier details
from fastapi import HTTPException, status
from app.core.email_utils import send_email # Neu
from fastapi_mail import MessageType # Neu
from app.core.config import settings # Neu
from datetime import date # For payout_date type consistency

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


# --- Modified create_payout_for_supplier to be async and send email ---
async def create_payout_for_supplier(db: Session, payout_in: PayoutCreate) -> Payout:
    supplier = supplier_service.get_supplier(db, supplier_id=payout_in.supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    if not supplier.email:
        # Depending on policy, this could be a hard error or just a warning where payout is created but no email sent.
        # For now, let's make it a hard error to enforce data quality.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier {supplier.supplier_number} ({supplier.first_name or ''} {supplier.last_name or ''}) has no email address configured. Payout cannot be created without a notification email address."
        )

    eligible_sale_items = db.query(SaleItem)\
        .join(Product, SaleItem.product_id == Product.id)\
        .filter(Product.supplier_id == payout_in.supplier_id)\
        .filter(Product.product_type == ProductTypeEnum.COMMISSION)\
        .filter(SaleItem.payout_id.is_(None))\
        .filter(SaleItem.commission_amount_at_sale > Decimal("0.00"))\
        .filter(Product.status == ProductStatusEnum.SOLD)\
        .all()

    if not eligible_sale_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No eligible items found for payout for this supplier.")

    total_payout_amount = sum(item.commission_amount_at_sale for item in eligible_sale_items)

    if total_payout_amount <= Decimal("0.00"):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total payout amount is zero or less, nothing to pay out.")

    payout_number = _generate_payout_number(db) # Sync function call

    payout_date_to_use: date = payout_in.payout_date if payout_in.payout_date else func.current_date() # type: ignore
    # If func.current_date() is used, it will be resolved by DB. For email, we might want Python's date.today()
    if payout_date_to_use == func.current_date(): # type: ignore
        effective_payout_date = date.today()
    else:
        effective_payout_date = payout_date_to_use # type: ignore

    db_payout = Payout(
        payout_number=payout_number,
        supplier_id=payout_in.supplier_id,
        payout_date=payout_date_to_use, # type: ignore
        total_amount=total_payout_amount,
        notes=payout_in.notes
    )

    db.add(db_payout)
    try:
        db.flush() # Get db_payout.id for linking items
    except Exception as e:
        db.rollback()
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during payout creation (flush phase): {str(e)}")

    for item in eligible_sale_items:
        item.payout_id = db_payout.id
        db.add(item) # Add item to session to mark it for update

    try:
        db.commit()
        db.refresh(db_payout) # Refresh to get all fields populated, including DB defaults like created_at

        # Send email notification
        email_subject = f"Ihre Auszahlung {db_payout.payout_number} von {settings.PROJECT_NAME}"

        # Construct a more detailed body if needed, perhaps with a summary of items or a link
        # For now, a simple notification.
        email_body_text = (
            f"Guten Tag {supplier.first_name or ''} {supplier.last_name or ''},\n\n"
            f"eine Auszahlung über {db_payout.total_amount:.2f} EUR mit der Nummer {db_payout.payout_number} "
            f"wurde für Sie am {effective_payout_date.strftime('%d.%m.%Y')} veranlasst und die zugehörigen Artikel wurden abgerechnet.\n\n"
            # Consider adding a link to a frontend page for this payout if available:
            # f"Details finden Sie unter: {settings.FRONTEND_URL}/payouts/{db_payout.id}\n\n"
            f"Vielen Dank für Ihre Zusammenarbeit.\n\n"
            f"Mit freundlichen Grüßen,\n"
            f"Ihr Team von {settings.PROJECT_NAME}"
        )

        if supplier.email: # Should always be true due to check above, but as safeguard
            email_sent = await send_email( # This is now an async call
                recipients=[supplier.email],
                subject=email_subject,
                body=email_body_text,
                subtype=MessageType.plain
            )
            if not email_sent:
                # Log that email sending failed. The payout is already committed.
                # This situation might require manual follow-up or a retry mechanism for emails.
                # For now, we just log (logging happens within send_email).
                # Consider adding a field to Payout model: email_notification_status (e.g., "SENT", "FAILED")
                pass

        # Eager load supplier and items for the response
        # Note: After an async operation (await send_email), the original db session might behave unexpectedly
        # if not handled correctly with FastAPI's async context.
        # However, FastAPI's Depends(get_db) typically handles session per request.
        # Re-querying might be safer if issues arise, but usually refresh after commit is fine.

        # To ensure the returned object is fully loaded and fresh after async operations:
        refreshed_payout = db.query(Payout).options(
            joinedload(Payout.supplier),
            selectinload(Payout.items_paid_out).joinedload(SaleItem.product)
        ).filter(Payout.id == db_payout.id).first()
        return refreshed_payout # type: ignore

    except Exception as e:
        db.rollback()
        # Log error e (include payout_number and supplier_id for context)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not complete payout transaction or send notification: {str(e)}")
