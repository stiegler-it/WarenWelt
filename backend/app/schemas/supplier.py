from typing import Optional

from pydantic import BaseModel


# Shared properties
class SupplierBase(BaseModel):
    name: Optional[str] = None


# Properties to receive on supplier creation
class SupplierCreate(SupplierBase):
    name: str


# Properties to receive on supplier update
class SupplierUpdate(SupplierBase):
    pass


# Properties shared by models stored in DB
class SupplierInDBBase(SupplierBase):
    id: int
    name: str

    class Config:
        orm_mode = True


# Properties to return to client
class Supplier(SupplierInDBBase):
    pass


# Properties stored in DB
class SupplierInDB(SupplierInDBBase):
    pass
