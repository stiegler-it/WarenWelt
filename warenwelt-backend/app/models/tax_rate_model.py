from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base

class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    rate_percent = Column(DECIMAL(5, 2), nullable=False)
    is_default_rate = Column(Boolean, default=False)
    # description = Column(String(255), nullable=True) # Aus DB-Struktur, kann später hinzugefügt werden

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now()) # Braucht ggf. Anpassung für SQLite

    products = relationship("Product", back_populates="tax_rate")
    # rental_contracts = relationship("RentalContract", back_populates="tax_rate") # Wenn RentalContract Model existiert
