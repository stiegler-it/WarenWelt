from sqlalchemy import Column, Integer, String, DECIMAL, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum
from datetime import date # Required for type hint if used in Pydantic, not strictly for SQLAlchemy model here

class RentalContractStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED" # Gekündigt
    PENDING = "PENDING" # Zukünftiger Vertrag

class RentalContract(Base):
    __tablename__ = "rental_contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String(50), unique=True, index=True, nullable=False) # Generated or manual

    shelf_id = Column(Integer, ForeignKey("shelves.id"), nullable=False)
    shelf = relationship("Shelf", back_populates="rental_contracts")

    # For tenants, we can link to Supplier if suppliers can also be tenants.
    # Or create a new Tenant model if they are distinct entities.
    # For now, let's assume a supplier can be a tenant.
    tenant_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    tenant = relationship("Supplier") # If Supplier model is named 'Supplier'

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False) # Laufzeitende
    # Alternative: duration_months = Column(Integer, nullable=False) and calculate end_date

    rent_price_at_signing = Column(DECIMAL(10, 2), nullable=False) # Price agreed upon, might differ from current shelf.monthly_rent_price
    payment_terms = Column(String(255), nullable=True) # e.g., "Monthly in advance"

    status = Column(SQLAlchemyEnum(RentalContractStatusEnum, name="rental_contract_status_enum"), nullable=False, default=RentalContractStatusEnum.PENDING)

    # Link to generated rental invoices
    rental_invoices = relationship("RentalInvoice", back_populates="rental_contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RentalContract(id={self.id}, contract_number='{self.contract_number}', shelf_id={self.shelf_id}, tenant_id={self.tenant_supplier_id})>"
