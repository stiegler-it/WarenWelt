from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List
from app.models.shelf_model import ShelfStatusEnum # Ensure this path is correct

# Base properties shared by other schemas
class ShelfBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Regal A1")
    location_description: Optional[str] = Field(None, max_length=255, example="Fensterseite")
    size_description: Optional[str] = Field(None, max_length=100, example="100x50cm")
    monthly_rent_price: Decimal = Field(..., gt=0, decimal_places=2, example=50.00)
    status: ShelfStatusEnum = Field(default=ShelfStatusEnum.AVAILABLE, example=ShelfStatusEnum.AVAILABLE)
    is_active: bool = Field(default=True)

# Properties to receive via API on creation
class ShelfCreate(ShelfBase):
    pass

# Properties to receive via API on update
class ShelfUpdate(ShelfBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    monthly_rent_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    status: Optional[ShelfStatusEnum] = None
    is_active: Optional[bool] = None

# Properties to return to client
class ShelfRead(ShelfBase):
    id: int

    class Config:
        orm_mode = True # Compatibility with SQLAlchemy models (pydantic v1)
        # from_attributes = True # for pydantic v2

# Minimal info for embedding in other schemas, e.g., RentalContractRead
class ShelfBasicRead(BaseModel):
    id: int
    name: str
    monthly_rent_price: Decimal
    status: ShelfStatusEnum

    class Config:
        orm_mode = True
        # from_attributes = True
