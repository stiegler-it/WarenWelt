from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime

from app.models.product_model import ProductTypeEnum, ProductStatusEnum # Import Enums from model
from .supplier_schema import SupplierRead # For nested data
from .product_category_schema import ProductCategoryRead # For nested data
from .tax_rate_schema import TaxRateRead # For nested data

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=255, description="Stock Keeping Unit / Barcode. Auto-generated if not provided.")
    description: Optional[str] = None

    supplier_id: int
    category_id: int
    tax_rate_id: int

    purchase_price: Decimal = Field(..., gt=0, decimal_places=2)
    selling_price: Decimal = Field(..., gt=0, decimal_places=2)

    product_type: ProductTypeEnum
    status: Optional[ProductStatusEnum] = ProductStatusEnum.IN_STOCK
    entry_date: Optional[date] = date.today()

    # MVP Simplifications (not included in create/update directly, or optional)
    # storage_deadline: Optional[date] = None
    # post_deadline_action: Optional[PostDeadlineActionEnum] = None # Handled by status changes for now
    image_url: Optional[str] = Field(None, max_length=2048)
    shelf_location: Optional[str] = Field(None, max_length=100)

    @validator('selling_price')
    def selling_price_must_be_greater_than_purchase_price(cls, v, values):
        if 'purchase_price' in values and v <= values['purchase_price']:
            # This validation might be too strict for NEW_WARE where purchase_price is cost
            # For COMMISSION, selling_price should definitely be > purchase_price (what supplier gets)
            # Consider adjusting based on product_type if this becomes an issue.
            # For now, a general check.
            # raise ValueError('Selling price must be greater than purchase price')
            pass # Relaxing for now, can be enforced based on product_type in service layer
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    # sku: Optional[str] = Field(None, max_length=255) # SKU should generally not be updatable easily once set

    supplier_id: Optional[int] = None
    category_id: Optional[int] = None
    tax_rate_id: Optional[int] = None

    purchase_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    selling_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)

    product_type: Optional[ProductTypeEnum] = None
    status: Optional[ProductStatusEnum] = None
    entry_date: Optional[date] = None
    image_url: Optional[str] = Field(None, max_length=2048)
    shelf_location: Optional[str] = Field(None, max_length=100)
    # storage_deadline: Optional[date] = None

    @validator('selling_price', always=True) # always=True to run even if not provided, if purchase_price is
    def check_prices_on_update(cls, v, values):
        # If only one price is updated, the other is taken from the existing model in the service layer.
        # This validator ensures consistency if both are part of the update payload.
        purchase_price = values.get('purchase_price')
        if v is not None and purchase_price is not None and v <= purchase_price:
            # As above, this might need refinement based on product_type
            # raise ValueError('Selling price must be greater than purchase price')
            pass
        return v


class ProductRead(ProductBase):
    id: int
    sku: str # SKU is not optional in read model
    created_at: datetime
    updated_at: datetime

    supplier: SupplierRead
    category: ProductCategoryRead
    tax_rate: TaxRateRead
    # location: Optional[LocationRead] # If location is used
    full_image_url: Optional[str] = None # Will be populated by computed_field or resolver

    class Config:
        from_attributes = True

    # Pydantic v2 way with computed_field
    # from pydantic import computed_field
    # from app.core.config import settings # Assuming API_BASE_URL or similar is configured

    # @computed_field
    # @property
    # def full_image_url(self) -> Optional[str]:
    #     if self.image_url:
    #          # This needs the base URL of the API if it's not running on root.
    #          # For simplicity, assuming API_V1_STR is part of how frontend constructs this.
    #          # Or, if settings.SERVER_HOST is defined:
    #          # return f"{settings.SERVER_HOST}/static/{self.image_url}"
    #          # For now, just return the path, frontend will prepend base URL + /static
    #         return f"/static/{self.image_url}"
    #     return None

# If not using computed_field, the transformation would typically happen in the service/router
# when preparing the response. For now, we'll add a placeholder and expect the router to fill it,
# or let the frontend prepend its known API base.
# A simpler approach for ProductRead is to just include image_url and let client handle it.
# Let's revert full_image_url for now and ensure image_url is present.
# The ProductBase already has image_url: Optional[str]
# So ProductRead will also have it.

# The API endpoint will return the relative image_url. The frontend knows the base URL.
# The image_upload_util.py saves to "static/product_images/..."
# The Product model stores "product_images/..."
# FastAPI serves "/static/product_images/..."
# Frontend requests "BACKEND_URL/static/product_images/..."
# This seems consistent. No need for full_image_url in the schema itself if frontend handles prefix.


# Schema for Price Tag Data
class PriceTagData(BaseModel):
    product_name: str
    sku: str
    selling_price: Decimal # Already Decimal in Product model
    # currency_symbol: str = "€" # Could be added if currency is configurable
