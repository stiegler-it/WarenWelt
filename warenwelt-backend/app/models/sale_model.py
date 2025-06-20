from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base
# from app.models.product_model import Product # Circular dependency if Product imports SaleItem, handle with string reference or post-init

class PaymentMethodEnum(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    VOUCHER = "VOUCHER" # Gutschein
    MIXED = "MIXED" # Gemischt

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(50), unique=True, index=True, nullable=False) # E.g., generated receipt number

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # FK to users (Mitarbeiter)
    user = relationship("User") # Add back_populates="sales" to User model if needed

    # location_id = Column(Integer, ForeignKey("locations.id"), nullable=False) # For MVP, single location assumed
    # location = relationship("Location")

    # customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True) # Optional, if customer tracking is implemented
    # customer = relationship("Customer")

    total_amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodEnum, name="payment_method_enum"), nullable=False)

    transaction_time = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Items associated with this sale
    items = relationship("SaleItem", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    sale = relationship("Sale", back_populates="items")

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    # Use a string reference for Product if Product model also refers to SaleItem to break circular dependency potential at import time
    product = relationship("Product") # Add back_populates="sale_items" to Product model

    quantity = Column(Integer, nullable=False, default=1) # Usually 1 for secondhand, but good to have
    price_at_sale = Column(DECIMAL(10, 2), nullable=False) # Historical price from Product.selling_price

    # For commission items, what the supplier gets for this item in this sale
    commission_amount_at_sale = Column(DECIMAL(10, 2), nullable=False) # Historical from Product.purchase_price for commission items

    # is_returned = Column(Boolean, default=False) # For MVP, returns are handled by changing product status directly

    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True) # Link to payout, if this item is included
    payout = relationship("Payout", back_populates="items_paid_out")

    def __repr__(self):
        return f"<SaleItem(id={self.id}, sale_id={self.sale_id}, product_id={self.product_id}, price={self.price_at_sale})>"
