from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    payout_number = Column(String(50), unique=True, index=True, nullable=False) # E.g., generated payout reference

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier = relationship("Supplier") # Add back_populates="payouts" to Supplier model if needed

    payout_date = Column(Date, nullable=False, default=func.current_date())
    total_amount = Column(DECIMAL(10, 2), nullable=False) # Total amount paid out to supplier

    notes = Column(Text, nullable=True) # Optional notes for the payout

    created_at = Column(TIMESTAMP, server_default=func.now())
    # updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now()) # Not typically updated

    # This relationship will collect all SaleItems included in this payout
    # This requires SaleItem to have a payout_id ForeignKey
    items_paid_out = relationship("SaleItem", back_populates="payout")


    def __repr__(self):
        return f"<Payout(id={self.id}, payout_number='{self.payout_number}', supplier_id={self.supplier_id}, amount={self.total_amount})>"
