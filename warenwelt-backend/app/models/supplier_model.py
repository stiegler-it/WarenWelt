from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_number = Column(String(50), unique=True, index=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True) # Should be nullable if not always present
    phone = Column(String(50), nullable=True)

    # For MVP, user_id link is optional and can be added later if supplier portal is implemented.
    # user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    # user = relationship("User", back_populates="supplier_profile") # Requires a 'supplier_profile' on User model

    is_internal = Column(Boolean, default=False) # For "Eigener Bestand"

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    products = relationship("Product", back_populates="supplier")

    # Ensure at least company_name or (first_name and last_name) is present.
    # This logic would typically be in the service/validation layer, not directly in DB model for simple cases.
    # __table_args__ = (
    #     CheckConstraint(
    #         or_(
    #             company_name.isnot(None),
    #             and_(first_name.isnot(None), last_name.isnot(None))
    #         ),
    #         name='ck_supplier_name_not_null'
    #     ),
    # )
