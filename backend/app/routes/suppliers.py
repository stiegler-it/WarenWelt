from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.schemas.supplier import Supplier, SupplierCreate, SupplierUpdate
from app.models.user import User
from app.routes import deps

router = APIRouter()


@router.get("/", response_model=List[Supplier])
def read_suppliers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve suppliers.
    """
    suppliers = crud.supplier.get_multi(db, skip=skip, limit=limit)
    return suppliers


@router.post("/", response_model=Supplier)
def create_supplier(
    *,
    db: Session = Depends(deps.get_db),
    supplier_in: SupplierCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new supplier.
    """
    supplier = crud.supplier.create(db=db, obj_in=supplier_in)
    return supplier


@router.put("/{id}", response_model=Supplier)
def update_supplier(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    supplier_in: SupplierUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a supplier.
    """
    supplier = crud.supplier.get(db=db, id=id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier = crud.supplier.update(db=db, db_obj=supplier, obj_in=supplier_in)
    return supplier


@router.get("/{id}", response_model=Supplier)
def read_supplier(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get supplier by ID.
    """
    supplier = crud.supplier.get(db=db, id=id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.delete("/{id}", response_model=Supplier)
def delete_supplier(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a supplier.
    """
    supplier = crud.supplier.get(db=db, id=id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier = crud.supplier.remove(db=db, id=id)
    return supplier
