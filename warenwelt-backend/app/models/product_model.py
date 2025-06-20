from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP, ForeignKey, Date, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base

class ProductTypeEnum(str, enum.Enum):
    COMMISSION = "COMMISSION"
    NEW_WARE = "NEW_WARE"

class ProductStatusEnum(str, enum.Enum):
    IN_STOCK = "IN_STOCK"
    SOLD = "SOLD"
    RETURNED = "RETURNED" # To supplier or for refund
    DONATED = "DONATED"
    RESERVED = "RESERVED"
    # PENDING_PAYOUT = "PENDING_PAYOUT" # Could be useful later

# For MVP, post_deadline_action is simplified or handled manually.
# class PostDeadlineActionEnum(str, enum.Enum):
#     RETURN_TO_SUPPLIER = "RETURN_TO_SUPPLIER"
#     DONATE = "DONATE"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), unique=True, index=True, nullable=False) # Stock Keeping Unit / Barcode
    name = Column(String(255), nullable=False, index=True)
    description = Column(String, nullable=True)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier = relationship("Supplier") #, back_populates="products") # Add back_populates to Supplier model

    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    category = relationship("ProductCategory") #, back_populates="products") # Add back_populates to ProductCategory model

    # location_id = Column(Integer, ForeignKey("locations.id"), nullable=False) # For MVP, assume single location or handle differently
    # location = relationship("Location") # Add if Location model is used

    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id"), nullable=False)
    tax_rate = relationship("TaxRate") #, back_populates="products") # Add back_populates to TaxRate model

    purchase_price = Column(DECIMAL(10, 2), nullable=False) # What the supplier gets (for commission) or cost price (for new ware)
    selling_price = Column(DECIMAL(10, 2), nullable=False) # What the customer pays

    product_type = Column(SQLAlchemyEnum(ProductTypeEnum, name="product_type_enum"), nullable=False)
    status = Column(SQLAlchemyEnum(ProductStatusEnum, name="product_status_enum"), default=ProductStatusEnum.IN_STOCK, nullable=False)

    entry_date = Column(Date, nullable=False, default=func.current_date())

    # MVP Simplifications:
    # storage_deadline = Column(Date, nullable=True)
    # post_deadline_action = Column(SQLAlchemyEnum(PostDeadlineActionEnum, name="post_deadline_action_enum"), nullable=True)
    image_url = Column(String(2048), nullable=True)
    shelf_location = Column(String(100), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    sale_items = relationship("SaleItem", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"
