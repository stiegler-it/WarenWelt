from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey #TIMESTAMP, Boolean
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func

from app.db.session import Base

class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)

    # For MVP, these are excluded as per plan:
    # parent_category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    differential_tax_surcharge_percent = Column(DECIMAL(5, 2), nullable=True, default=0.00)
    # description = Column(String(255), nullable=True)

    # children = relationship("ProductCategory", backref=backref('parent', remote_side=[id]))
    products = relationship("Product", back_populates="category")

    # created_at = Column(TIMESTAMP, server_default=func.now())
    # updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
