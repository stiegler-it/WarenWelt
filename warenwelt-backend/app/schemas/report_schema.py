from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Dict, List

class DailySalesReportItem(BaseModel):
    payment_method: str # From PaymentMethodEnum
    total_amount: Decimal = Field(..., decimal_places=2)
    transaction_count: int

class DailySummaryReport(BaseModel):
    report_date: date
    overall_total_amount: Decimal = Field(..., decimal_places=2)
    overall_transaction_count: int
    summary_by_payment_method: List[DailySalesReportItem]
    total_commission_paid_to_suppliers: Optional[Decimal] = Field(None, decimal_places=2) # Summe der product.purchase_price für verkaufte Kommissionsartikel
    # Could add more details like total tax etc. later.

# Optional: Schema for query parameters if needed, though date can be a path/query param directly.
# class DailySummaryRequest(BaseModel):
#     date: date

# --- Period Summary (Weekly/Monthly) ---
class PeriodSummaryReportItem(DailySalesReportItem): # Inherits from DailySalesReportItem
    # Potentially add more fields specific to period summaries if needed later
    pass

class PeriodSummaryReport(BaseModel):
    report_type: str # "WEEKLY" or "MONTHLY"
    start_date: date
    end_date: date
    overall_total_amount: Decimal = Field(..., decimal_places=2)
    overall_transaction_count: int
    summary_by_payment_method: List[PeriodSummaryReportItem]
    total_commission_paid_to_suppliers: Optional[Decimal] = Field(None, decimal_places=2)
    # Optional: Could include a list of daily summaries if detailed breakdown is needed
    # daily_breakdown: Optional[List[DailySummaryReport]] = None


# --- Revenue List Report (with new ware and differential taxation indicators) ---
class RevenueItem(BaseModel): # Represents a line item in a sale, focused on revenue aspects
    product_id: int
    product_sku: str
    product_name: str
    product_type: str # From ProductTypeEnum (e.g., "COMMISSION", "NEW_WARE")

    quantity_sold: int

    # Pricing and Revenue
    price_per_unit_at_sale: Decimal = Field(..., decimal_places=2) # Selling price per unit at time of sale
    total_gross_revenue_for_item: Decimal = Field(..., decimal_places=2) # quantity_sold * price_per_unit_at_sale

    # Cost and Commission (relevant for profit calculation and supplier payout)
    purchase_price_per_unit: Optional[Decimal] = Field(None, decimal_places=2) # Cost of goods for NEW_WARE, or supplier's take for COMMISSION
    total_cost_or_commission_for_item: Optional[Decimal] = Field(None, decimal_places=2) # quantity_sold * purchase_price_per_unit

    # Taxation details (simplified for now, requires more detailed tax model/logic for accuracy)
    # This is a placeholder; actual tax calculation needs to be robust.
    # For differential taxation, tax is on the margin, not the full selling price.
    # For new ware, tax is typically on the selling price.
    tax_rate_percentage_at_sale: Optional[Decimal] = Field(None, decimal_places=2) # e.g., 19.00 for 19%
    # calculated_tax_amount_for_item: Decimal = Field(..., decimal_places=2) # This would be complex to generalize here

    # Differential Taxation Flags/Fields (conceptual)
    # is_potentially_differential_taxed: bool = False # True if product_type is COMMISSION/USED and meets criteria
    # margin_for_differential_tax: Optional[Decimal] = None # (selling_price - purchase_price) if diff. taxed
    # tax_on_margin: Optional[Decimal] = None # Tax amount if diff. taxed

    # Sale context
    sale_id: int
    transaction_number: str
    sale_transaction_time: datetime # from datetime import datetime

    class Config:
        orm_mode = True
        # from_attributes = True # Pydantic v2

class RevenueListReport(BaseModel):
    report_generated_at: datetime
    report_period_start_date: date
    report_period_end_date: date

    total_gross_revenue_all_items: Decimal = Field(..., decimal_places=2)
    total_items_sold: int

    # Summary by Product Type
    summary_by_product_type: Dict[str, Dict[str, Decimal]] = Field(..., example={
        "NEW_WARE": {"total_revenue": 1500.00, "total_cost": 800.00, "item_count": 50},
        "COMMISSION": {"total_revenue": 2500.00, "total_supplier_payout": 1250.00, "item_count": 70}
    })

    # Placeholder for aggregated tax information - very complex
    # aggregated_tax_summary: Dict[str, Decimal] = Field(..., example={"VAT_19_on_new_ware": 200.00, "VAT_on_diff_margin": 50.00})

    revenue_items: List[RevenueItem]
