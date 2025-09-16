from sqlalchemy.orm import Session

from app import crud
from app.schemas.supplier import SupplierCreate


class SupplierService:
    def create_supplier(self, db: Session, *, obj_in: SupplierCreate):
        """
        Create a supplier.
        In a real application, this method could do more, e.g. validate the supplier
        against an external service.
        """
        return crud.supplier.create(db=db, obj_in=obj_in)


supplier_service = SupplierService()
