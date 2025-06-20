from pydantic import BaseModel, Field
from typing import Optional
# from datetime import datetime # If created_at/updated_at were in the model

class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    # description: Optional[str] = Field(None, max_length=255) # If added to model

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryUpdate(ProductCategoryBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255) # Make name optional for updates
    pass

class ProductCategoryRead(ProductCategoryBase):
    id: int
    # created_at: datetime # If added to model
    # updated_at: datetime # If added to model

    class Config:
        from_attributes = True
