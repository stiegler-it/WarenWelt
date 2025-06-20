from sqlalchemy import Column, Integer, String, DECIMAL, Date, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum
from datetime import date as py_date # Alias to avoid conflict

class RentalInvoiceStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"       # Entwurf, noch nicht finalisiert
    OPEN = "OPEN"         # Finalisiert, Zahlung erwartet
    PAID = "PAID"         # Vollständig bezahlt
    OVERDUE = "OVERDUE"   # Überfällig
    CANCELLED = "CANCELLED" # Storniert

class RentalInvoice(Base):
    __tablename__ = "rental_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False) # E.g., RENT-YYYY-MM-XXXX

    rental_contract_id = Column(Integer, ForeignKey("rental_contracts.id"), nullable=False)
    # Add back_populates="rental_invoices" to RentalContract model later
    rental_contract = relationship("RentalContract", back_populates="rental_invoices")

    tenant_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False) # Denormalized for easier querying/reporting
    tenant = relationship("Supplier")

    shelf_id = Column(Integer, ForeignKey("shelves.id"), nullable=False) # Denormalized
    shelf = relationship("Shelf")

    invoice_date = Column(Date, nullable=False, default=py_date.today)
    due_date = Column(Date, nullable=False) # Zahlungsziel

    billing_period_start = Column(Date, nullable=False) # Abrechnungszeitraum Anfang
    billing_period_end = Column(Date, nullable=False)   # Abrechnungszeitraum Ende

    amount_due = Column(DECIMAL(10, 2), nullable=False) # Rechnungsbetrag
    amount_paid = Column(DECIMAL(10, 2), nullable=True, default=0.00) # Bereits bezahlter Betrag

    status = Column(SQLAlchemyEnum(RentalInvoiceStatusEnum, name="rental_invoice_status_enum"), nullable=False, default=RentalInvoiceStatusEnum.DRAFT)

    notes = Column(Text, nullable=True) # Zusätzliche Anmerkungen auf der Rechnung

    # payment_details = Column(Text, nullable=True) # Details zur Zahlung, falls erfolgt (z.B. Transaktions-ID)
    # created_at, updated_at if needed via a BaseMixin or similar

    def __repr__(self):
        return f"<RentalInvoice(id={self.id}, invoice_number='{self.invoice_number}', status='{self.status.value}')>"
