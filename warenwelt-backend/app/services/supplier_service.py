from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.supplier_model import Supplier
from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate

def get_supplier(db: Session, supplier_id: int) -> Optional[Supplier]:
    return db.query(Supplier).filter(Supplier.id == supplier_id).first()

def get_supplier_by_supplier_number(db: Session, supplier_number: str) -> Optional[Supplier]:
    return db.query(Supplier).filter(Supplier.supplier_number == supplier_number).first()

def get_supplier_by_email(db: Session, email: str) -> Optional[Supplier]:
    return db.query(Supplier).filter(Supplier.email == email).first()

def get_suppliers(db: Session, skip: int = 0, limit: int = 100) -> List[Supplier]:
    return db.query(Supplier).offset(skip).limit(limit).all()

def create_supplier(db: Session, supplier: SupplierCreate) -> Supplier:
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def update_supplier(db: Session, db_supplier: Supplier, supplier_in: SupplierUpdate) -> Supplier:
    update_data = supplier_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)

    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def delete_supplier(db: Session, supplier_id: int) -> Optional[Supplier]:
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if db_supplier:
        # Add logic here to check if supplier can be deleted (e.g., no associated products)
        # For MVP, we allow direct deletion.
        # if db_supplier.products: # Assuming 'products' relationship exists
        #     raise ValueError("Supplier has associated products and cannot be deleted.")
        db.delete(db_supplier)
        db.commit()
    return db_supplier
