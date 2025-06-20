from pydantic import BaseModel, Field
from typing import Optional
# from datetime import datetime # If created_at/updated_at were in the model

from decimal import Decimal

class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    differential_tax_surcharge_percent: Optional[Decimal] = Field(0.00, ge=0, le=100, decimal_places=2)
    # description: Optional[str] = Field(None, max_length=255) # If added to model

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryUpdate(BaseModel): # Changed from ProductCategoryBase to allow all fields to be optional
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    differential_tax_surcharge_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    # description: Optional[str] = Field(None, max_length=255)

class ProductCategoryRead(ProductCategoryBase):
    id: int
    # created_at: datetime # If added to model
    # updated_at: datetime # If added to model
    # differential_tax_surcharge_percent is inherited from ProductCategoryBase

    class Config:
        from_attributes = True
