from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.tax_rate_model import TaxRate
from app.schemas.tax_rate_schema import TaxRateCreate

def get_tax_rate(db: Session, tax_rate_id: int) -> Optional[TaxRate]:
    return db.query(TaxRate).filter(TaxRate.id == tax_rate_id).first()

def get_tax_rate_by_name(db: Session, name: str) -> Optional[TaxRate]:
    return db.query(TaxRate).filter(TaxRate.name == name).first()

def get_tax_rates(db: Session, skip: int = 0, limit: int = 100) -> List[TaxRate]:
    return db.query(TaxRate).offset(skip).limit(limit).all()

def create_tax_rate(db: Session, tax_rate: TaxRateCreate) -> TaxRate:
    db_tax_rate = TaxRate(
        name=tax_rate.name,
        rate_percent=tax_rate.rate_percent,
        is_default_rate=tax_rate.is_default_rate
        # description=tax_rate.description
    )
    db.add(db_tax_rate)
    db.commit()
    db.refresh(db_tax_rate)
    return db_tax_rate

def get_default_tax_rate(db: Session) -> Optional[TaxRate]:
    return db.query(TaxRate).filter(TaxRate.is_default_rate == True).first()
