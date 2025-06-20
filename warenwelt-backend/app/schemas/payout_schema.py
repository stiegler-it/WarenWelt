from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from .supplier_schema import SupplierRead # For displaying supplier details
from .sale_schema import SaleItemRead # For displaying items included in a payout (optional detail)

# Schema for querying items eligible for payout for a supplier
class PayoutSummaryItem(BaseModel):
    product_id: int
    product_sku: str
    product_name: str
    sale_id: int
    sale_transaction_number: str
    sale_date: datetime
    commission_amount: Decimal # from SaleItem.commission_amount_at_sale

class SupplierPayoutSummary(BaseModel):
    supplier_id: int
    supplier_name: str # company_name or first/last name
    total_due: Decimal
    eligible_items_count: int
    items_preview: List[PayoutSummaryItem] # A preview of some items

# Payout Schemas
class PayoutBase(BaseModel):
    supplier_id: int
    payout_date: Optional[date] = date.today()
    # total_amount will be calculated by the service or validated against calculated
    notes: Optional[str] = None

class PayoutCreate(PayoutBase):
    # The service will calculate the total_amount based on unpaid items for the supplier.
    # Or, an explicit list of sale_item_ids could be passed to be included in the payout.
    # For MVP: create payout for ALL currently unpaid items for the supplier.
    # A specific amount might be passed for partial payout, but this complicates logic.
    # Let's assume it pays out the full currently due amount.
    pass


class PayoutRead(PayoutBase):
    id: int
    payout_number: str
    total_amount: Decimal # This is crucial
    supplier: SupplierRead # Embed supplier details
    created_at: datetime
    items_paid_out: List[SaleItemRead] # Show which items were part of this payout

    class Config:
        from_attributes = True
