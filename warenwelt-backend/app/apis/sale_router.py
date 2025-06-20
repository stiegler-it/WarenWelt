from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas import sale_schema
from app.services import sale_service
from app.core.security import get_current_active_user
from app.models.user_model import User as UserModel # For type hint

router = APIRouter()

@router.post("/", response_model=sale_schema.SaleRead, status_code=status.HTTP_201_CREATED)
def create_new_sale(
    sale_in: sale_schema.SaleCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        created_sale = sale_service.create_sale(db=db, sale_in=sale_in, current_user=current_user)
        return created_sale
    except HTTPException as e:
        # Re-raise HTTPException to ensure FastAPI handles it correctly
        raise e
    except Exception as e:
        # Log the exception e
        # Consider a more generic error message for unexpected issues
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/", response_model=List[sale_schema.SaleRead])
def read_sales_list(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID (employee who made the sale)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # All sales are protected
):
    # Add permission check here if only admins/specific roles can see all sales
    # or if users can only see their own sales.
    # For MVP, any active user can list sales, potentially filtered by user_id.

    # If a non-admin user requests sales for another user_id, you might want to restrict it.
    # Example:
    # if not (current_user.role.name == "Admin" or current_user.id == user_id or user_id is None):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view sales for this user.")

    sales = sale_service.get_sales(db, skip=skip, limit=limit, user_id=user_id)
    return sales


@router.get("/{sale_id}", response_model=sale_schema.SaleRead)
def read_single_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_sale = sale_service.get_sale(db, sale_id=sale_id)
    if db_sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    # Permission check: e.g., user can see their own sales, or admin can see all.
    # if not (current_user.role.name == "Admin" or current_user.id == db_sale.user_id):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view this sale.")

    return db_sale
