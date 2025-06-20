from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

class ShelfStatusEnum(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    MAINTENANCE = "MAINTENANCE"

class Shelf(Base):
    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True) # e.g., "Regal A1", "Fläche X"
    location_description = Column(String(255), nullable=True) # e.g., "Fensterseite", "Ecke links"
    size_description = Column(String(100), nullable=True) # e.g., "100x50cm", "2 Fächer"
    monthly_rent_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(SQLAlchemyEnum(ShelfStatusEnum, name="shelf_status_enum"), nullable=False, default=ShelfStatusEnum.AVAILABLE)
    is_active = Column(Boolean, default=True) # Soft delete or deactivation

    rental_contracts = relationship("RentalContract", back_populates="shelf")

    def __repr__(self):
        return f"<Shelf(id={self.id}, name='{self.name}', status='{self.status.value}')>"
