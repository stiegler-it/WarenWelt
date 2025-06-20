from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class SupplierBase(BaseModel):
    supplier_number: str = Field(..., min_length=1, max_length=50)
    company_name: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    is_internal: Optional[bool] = False

    @validator('company_name', always=True)
    def check_name_present(cls, v, values):
        if not v and not (values.get('first_name') and values.get('last_name')):
            raise ValueError('Either company_name or both first_name and last_name must be provided')
        return v

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    # All fields are optional for update
    supplier_number: Optional[str] = Field(None, min_length=1, max_length=50)
    pass

class SupplierRead(SupplierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
