from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

class TaxRateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rate_percent: Decimal = Field(..., gt=0, decimal_places=2)
    is_default_rate: Optional[bool] = False
    # description: Optional[str] = None

class TaxRateCreate(TaxRateBase):
    pass

class TaxRateRead(TaxRateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic V2, formerly orm_mode = True
