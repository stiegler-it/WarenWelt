from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
import uuid # For transaction_number generation

from app.models import Product, Sale, SaleItem, User
from app.models.product_model import ProductStatusEnum, ProductTypeEnum
from app.schemas.sale_schema import SaleCreate, SaleItemCreate
from app.services import product_service # To fetch product details and update status
from fastapi import HTTPException, status

def _generate_transaction_number(db: Session) -> str:
    """Generates a unique transaction number for a sale."""
    # Example: "SALE-" + first 8 chars of a UUID + "-YYMMDD"
    # This is a basic example.
    while True:
        # date_str = datetime.now().strftime("%y%m%d")
        # transaction_number = f"TRX-{uuid.uuid4().hex[:8].upper()}-{date_str}"
        # Simplified for now
        transaction_number = f"TRX-{uuid.uuid4().hex[:12].upper()}"
        if not db.query(Sale).filter(Sale.transaction_number == transaction_number).first():
            return transaction_number

def create_sale(db: Session, sale_in: SaleCreate, current_user: User) -> Sale:
    db_items = []
    total_amount_calculated = Decimal("0.00")

    if not sale_in.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale must contain at least one item.")

    processed_product_ids = set()

    for item_in in sale_in.items:
        product: Optional[Product] = None
        if item_in.sku:
            product = product_service.get_product_by_sku(db, sku=item_in.sku)
        elif item_in.product_id:
            product = product_service.get_product(db, product_id=item_in.product_id)

        if not product:
            error_detail = f"Product with SKU '{item_in.sku}'" if item_in.sku else f"Product with ID '{item_in.product_id}'"
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{error_detail} not found.")

        if product.id in processed_product_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {product.sku} listed multiple times in the same sale.")
        processed_product_ids.add(product.id)

        if product.status != ProductStatusEnum.IN_STOCK:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product.sku} ({product.name}) is not IN_STOCK. Current status: {product.status.value}."
            )

        if item_in.quantity > 1 and product.product_type == ProductTypeEnum.COMMISSION:
             # Typically, commission items are unique, so quantity should be 1.
             # This check can be debated based on specific shop rules.
             pass # Allowing for now, but could be a validation point.

        price_at_sale = product.selling_price
        # For commission items, purchase_price is what the supplier gets.
        # For new ware, purchase_price is the cost of goods.
        # The `commission_amount_at_sale` field in SaleItem is specifically for the supplier's cut.
        commission_for_item = product.purchase_price if product.product_type == ProductTypeEnum.COMMISSION else Decimal("0.00")

        db_sale_item = SaleItem(
            product_id=product.id,
            quantity=item_in.quantity,
            price_at_sale=price_at_sale,
            commission_amount_at_sale=commission_for_item * item_in.quantity # Total commission for this line item
        )
        db_items.append(db_sale_item)
        total_amount_calculated += (price_at_sale * item_in.quantity)

    # Create the Sale object
    transaction_number = _generate_transaction_number(db)
    db_sale = Sale(
        transaction_number=transaction_number,
        user_id=current_user.id,
        payment_method=sale_in.payment_method,
        # customer_id=sale_in.customer_id, # If customer tracking is used
        total_amount=total_amount_calculated,
        items=db_items # Associate SaleItems with the Sale
    )

    db.add(db_sale)
    # db.flush() # Flush to get db_sale.id for items if items were not directly associated

    # Update product statuses
    for item_in_db in db_sale.items: # Iterate over the items now associated with the sale
        product_to_update = db.query(Product).filter(Product.id == item_in_db.product_id).first() # Re-fetch for safety
        if product_to_update:
            product_to_update.status = ProductStatusEnum.SOLD
            db.add(product_to_update)
        else:
            # This should not happen if initial checks were correct
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update product status during sale.")


    try:
        db.commit()
        db.refresh(db_sale)
        # Eager load items and their products for the response
        return db.query(Sale).options(
            joinedload(Sale.items).joinedload(SaleItem.product).joinedload(Product.supplier),
            joinedload(Sale.items).joinedload(SaleItem.product).joinedload(Product.category),
            joinedload(Sale.items).joinedload(SaleItem.product).joinedload(Product.tax_rate)
        ).filter(Sale.id == db_sale.id).first()
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not complete sale transaction: {str(e)}")


def get_sale(db: Session, sale_id: int) -> Optional[Sale]:
    return db.query(Sale).options(
        joinedload(Sale.items).joinedload(SaleItem.product).joinedload(Product.supplier),
        joinedload(Sale.items).joinedload(SaleItem.product).joinedload(Product.category),
        joinedload(Sale.items).joinedload(SaleItem.product).joinedload(Product.tax_rate),
        joinedload(Sale.user) # Eager load the user who made the sale
    ).filter(Sale.id == sale_id).first()

def get_sales(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None
    # Add other filters like date range, payment_method etc. if needed
) -> List[Sale]:
    query = db.query(Sale).options(
        joinedload(Sale.items).joinedload(SaleItem.product), # Minimal product info for list
        joinedload(Sale.user)
    )
    if user_id is not None:
        query = query.filter(Sale.user_id == user_id)

    return query.order_by(Sale.transaction_time.desc()).offset(skip).limit(limit).all()


from datetime import date, datetime, time
from app.schemas.report_schema import DailySummaryReport, DailySalesReportItem
from app.models.sale_model import PaymentMethodEnum
from sqlalchemy import cast, Date as SQLDate, func as sqlfunc

def get_daily_sales_summary(db: Session, report_date: date) -> DailySummaryReport:
    start_datetime = datetime.combine(report_date, time.min)
    end_datetime = datetime.combine(report_date, time.max)

    # Query sales for the given date
    sales_on_date = db.query(Sale)\
        .filter(Sale.transaction_time >= start_datetime)\
        .filter(Sale.transaction_time <= end_datetime)\
        .all()

    overall_total_amount = Decimal("0.00")
    overall_transaction_count = len(sales_on_date)

    summary_by_payment_method_dict: Dict[str, Dict[str, any]] = {}

    for sale in sales_on_date:
        overall_total_amount += sale.total_amount
        payment_method_str = sale.payment_method.value # Get the string value of the enum

        if payment_method_str not in summary_by_payment_method_dict:
            summary_by_payment_method_dict[payment_method_str] = {
                "total_amount": Decimal("0.00"),
                "transaction_count": 0
            }

        summary_by_payment_method_dict[payment_method_str]["total_amount"] += sale.total_amount
        summary_by_payment_method_dict[payment_method_str]["transaction_count"] += 1

    # Convert dict to list of DailySalesReportItem
    summary_list = [
        DailySalesReportItem(
            payment_method=pm,
            total_amount=data["total_amount"],
            transaction_count=data["transaction_count"]
        ) for pm, data in summary_by_payment_method_dict.items()
    ]

    # Ensure all payment methods are present in the summary, even if count is 0
    # This makes frontend display easier.
    all_pm_values = [e.value for e in PaymentMethodEnum]
    existing_pm_in_summary = [item.payment_method for item in summary_list]

    for pm_value in all_pm_values:
        if pm_value not in existing_pm_in_summary:
            summary_list.append(DailySalesReportItem(
                payment_method=pm_value,
                total_amount=Decimal("0.00"),
                transaction_count=0
            ))

    summary_list.sort(key=lambda x: x.payment_method) # Sort for consistent order

    return DailySummaryReport(
        report_date=report_date,
        overall_total_amount=overall_total_amount,
        overall_transaction_count=overall_transaction_count,
        summary_by_payment_method=summary_list
    )
