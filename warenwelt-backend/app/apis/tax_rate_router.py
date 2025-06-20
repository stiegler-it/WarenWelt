from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas import tax_rate_schema
from app.services import tax_rate_service
from app.core.security import get_current_active_user # To protect endpoints
from app.models.user_model import User as UserModel # For type hint of current_user

router = APIRouter()

@router.post("/", response_model=tax_rate_schema.TaxRateRead, status_code=status.HTTP_201_CREATED)
def create_new_tax_rate(
    tax_rate_in: tax_rate_schema.TaxRateCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect endpoint
):
    # Optional: Check for admin rights if only admins can create tax rates
    # if not current_user.role or current_user.role.name != "Admin":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    existing_tax_rate = tax_rate_service.get_tax_rate_by_name(db, name=tax_rate_in.name)
    if existing_tax_rate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tax rate with name '{tax_rate_in.name}' already exists."
        )

    if tax_rate_in.is_default_rate:
        default_rate = tax_rate_service.get_default_tax_rate(db)
        if default_rate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A default tax rate ('{default_rate.name}') already exists. Only one can be default."
            )

    return tax_rate_service.create_tax_rate(db=db, tax_rate=tax_rate_in)


@router.get("/", response_model=List[tax_rate_schema.TaxRateRead])
def read_tax_rates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect endpoint
):
    tax_rates = tax_rate_service.get_tax_rates(db, skip=skip, limit=limit)
    return tax_rates


@router.get("/{tax_rate_id}", response_model=tax_rate_schema.TaxRateRead)
def read_tax_rate(
    tax_rate_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect endpoint
):
    db_tax_rate = tax_rate_service.get_tax_rate(db, tax_rate_id=tax_rate_id)
    if db_tax_rate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax rate not found")
    return db_tax_rate


# Placeholder for Update and Delete if needed for MVP
# @router.put("/{tax_rate_id}", response_model=tax_rate_schema.TaxRateRead)
# def update_tax_rate(...):
#     pass

# @router.delete("/{tax_rate_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_tax_rate(...):
#     pass
