from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas import supplier_schema
from app.services import supplier_service
from app.core.security import get_current_active_user
from app.models.user_model import User as UserModel # For type hint

router = APIRouter()

@router.post("/", response_model=supplier_schema.SupplierRead, status_code=status.HTTP_201_CREATED)
def create_new_supplier(
    supplier_in: supplier_schema.SupplierCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check for uniqueness of supplier_number
    existing_supplier_num = supplier_service.get_supplier_by_supplier_number(db, supplier_number=supplier_in.supplier_number)
    if existing_supplier_num:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with number '{supplier_in.supplier_number}' already exists."
        )
    # Check for uniqueness of email if provided
    if supplier_in.email:
        existing_supplier_email = supplier_service.get_supplier_by_email(db, email=supplier_in.email)
        if existing_supplier_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with email '{supplier_in.email}' already exists."
            )

    return supplier_service.create_supplier(db=db, supplier=supplier_in)


@router.get("/", response_model=List[supplier_schema.SupplierRead])
def read_suppliers_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    suppliers = supplier_service.get_suppliers(db, skip=skip, limit=limit)
    return suppliers


@router.get("/{supplier_id}", response_model=supplier_schema.SupplierRead)
def read_single_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_supplier = supplier_service.get_supplier(db, supplier_id=supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return db_supplier


@router.put("/{supplier_id}", response_model=supplier_schema.SupplierRead)
def update_single_supplier(
    supplier_id: int,
    supplier_in: supplier_schema.SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_supplier = supplier_service.get_supplier(db, supplier_id=supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    # Check for uniqueness if supplier_number is being changed
    if supplier_in.supplier_number and supplier_in.supplier_number != db_supplier.supplier_number:
        existing_supplier_num = supplier_service.get_supplier_by_supplier_number(db, supplier_number=supplier_in.supplier_number)
        if existing_supplier_num and existing_supplier_num.id != supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with number '{supplier_in.supplier_number}' already exists."
            )

    # Check for uniqueness if email is being changed
    if supplier_in.email and supplier_in.email != db_supplier.email:
        existing_supplier_email = supplier_service.get_supplier_by_email(db, email=supplier_in.email)
        if existing_supplier_email and existing_supplier_email.id != supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with email '{supplier_in.email}' already exists."
            )

    return supplier_service.update_supplier(db=db, db_supplier=db_supplier, supplier_in=supplier_in)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_single_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_supplier = supplier_service.get_supplier(db, supplier_id=supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    # Add more robust check if supplier is deletable (e.g. no active products)
    # For MVP, direct deletion.
    # if len(db_supplier.products) > 0: # Assuming products relationship
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete supplier with active products.")

    supplier_service.delete_supplier(db=db, supplier_id=supplier_id)
    return None
