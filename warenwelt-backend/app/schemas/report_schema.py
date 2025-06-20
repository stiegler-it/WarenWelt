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
    # Could add more details like total commission, total tax etc. later.

# Optional: Schema for query parameters if needed, though date can be a path/query param directly.
# class DailySummaryRequest(BaseModel):
#     date: date
