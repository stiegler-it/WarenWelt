from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import date
from typing import Optional
from app.models.rental_contract_model import RentalContractStatusEnum
from .shelf_schema import ShelfBasicRead

# TODO: Refactor SupplierBasicRead: Move to supplier_schema.py and import from there.
# Also, make ORM mode consistent across all schemas (orm_mode vs from_attributes)
class SupplierBasicRead(BaseModel):
    id: int
    supplier_number: str
    company_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.company_name:
            return self.company_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        # Fallback, consider if supplier_number should be the primary display or part of it.
        return self.supplier_number if self.supplier_number else f"Supplier ID: {self.id}"


    class Config:
        orm_mode = True
        # from_attributes = True # Pydantic v2

class RentalContractBase(BaseModel):
    shelf_id: int = Field(..., example=1)
    tenant_supplier_id: int = Field(..., example=1) # References Supplier.id
    start_date: date = Field(..., example=date(2024, 1, 1))
    end_date: date = Field(..., example=date(2024, 12, 31))
    rent_price_at_signing: Decimal = Field(..., gt=0, decimal_places=2, example=45.00)
    payment_terms: Optional[str] = Field(None, max_length=255, example="Monthly in advance")
    status: RentalContractStatusEnum = Field(default=RentalContractStatusEnum.PENDING, example=RentalContractStatusEnum.PENDING)
    contract_number: Optional[str] = Field(None, max_length=50, example="RC-2024-001") # Can be optional on create if auto-generated

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        # This validator runs when 'end_date' is provided in the input data.
        # 'values' contains other fields from the input data that have already been validated.
        if 'start_date' in values and values['start_date'] is not None:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v

class RentalContractCreate(RentalContractBase):
    pass

class RentalContractUpdate(BaseModel):
    # All fields are optional for an update operation.
    shelf_id: Optional[int] = None
    tenant_supplier_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rent_price_at_signing: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    payment_terms: Optional[str] = Field(None, max_length=255)
    status: Optional[RentalContractStatusEnum] = None
    contract_number: Optional[str] = Field(None, max_length=50)

    # For updates, validation logic that depends on existing model state
    # is typically handled in the service layer, after fetching the existing record.
    # A Pydantic validator here can only validate based on the fields present in the update payload.
    # If both start_date and end_date are in the payload, this validator can check them.
    @validator('end_date', always=True) # always=True to run even if end_date is None (to catch if start_date is set and makes existing end_date invalid)
    def validate_dates_in_payload(cls, v, values):
        start_date = values.get('start_date')
        end_date = v # Current value of end_date being validated

        if start_date is not None and end_date is not None:
            if end_date <= start_date:
                raise ValueError('End date must be after start date when both are provided.')
        return v

class RentalContractRead(RentalContractBase):
    id: int
    shelf: Optional[ShelfBasicRead] = None
    tenant: Optional[SupplierBasicRead] = None # tenant_supplier_id maps to Supplier

    class Config:
        orm_mode = True
        # from_attributes = True

# Update __init__.py in schemas
# No, this will be done by adding new files to the directory.
# Need to ensure the main __init__.py for schemas is updated if it selectively imports.

# For the validator in RentalContractUpdate:
# The service layer will be responsible for more complex cross-field validation
# against the existing database state. For example, if only 'start_date' is updated,
# the service must check it against the existing 'end_date' from the database.
# The Pydantic validator as written primarily handles consistency within the payload itself.
