from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas import product_schema
from app.services import product_service
from app.core.security import get_current_active_user
from app.models.user_model import User as UserModel # For type hint
from app.models.product_model import ProductStatusEnum


router = APIRouter()

@router.post("/", response_model=product_schema.ProductRead, status_code=status.HTTP_201_CREATED)
def create_new_product(
    product_in: product_schema.ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Service layer handles FK validation and SKU uniqueness
    try:
        created_product = product_service.create_product(db=db, product_in=product_in)
        return created_product
    except HTTPException as e: # Catch specific HTTPErrors from service
        raise e
    except Exception as e: # Catch any other unexpected errors
        # Log the error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/", response_model=List[product_schema.ProductRead])
def read_products_list(
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    status_filter: Optional[ProductStatusEnum] = Query(None, alias="status", description="Filter by product status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Convert enum to string if provided, as service expects string or None
    status_str = status_filter.value if status_filter else None
    products = product_service.get_products(
        db, skip=skip, limit=limit,
        supplier_id=supplier_id, category_id=category_id, status=status_str
    )
    return products


@router.get("/{product_id}", response_model=product_schema.ProductRead)
def read_single_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_product = product_service.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@router.get("/sku/{sku}", response_model=product_schema.ProductRead)
def read_single_product_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_product = product_service.get_product_by_sku(db, sku=sku)
    # Need to load relations for the response model if get_product_by_sku doesn't do it.
    # For consistency, fetching again with get_product if found by SKU.
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with SKU '{sku}' not found")

    # If get_product_by_sku doesn't eager load, fetch again to ensure full data for ProductRead
    # This is slightly inefficient but ensures the response model is correctly populated.
    # A better way would be for get_product_by_sku to also use joinedload.
    # For now, let's assume get_product_by_sku is simple and we refetch.
    # If get_product_by_sku is modified to eager load, this is not needed.
    full_db_product = product_service.get_product(db, product_id=db_product.id)
    if full_db_product is None: # Should not happen if db_product was found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with SKU '{sku}' not found (consistency issue).")

    return full_db_product


@router.put("/{product_id}", response_model=product_schema.ProductRead)
def update_single_product(
    product_id: int,
    product_in: product_schema.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_product = product_service.get_product(db, product_id=product_id) # get_product eager loads
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        updated_product = product_service.update_product(db=db, db_product=db_product, product_in=product_in)
        return updated_product
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during update: {str(e)}")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_single_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_product = product_service.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        product_service.delete_product(db=db, product_id=product_id)
    except HTTPException as e: # Catch specific errors like "cannot delete sold product"
        raise e
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during deletion: {str(e)}")

    return None
