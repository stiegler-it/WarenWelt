from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path

from app.db.session import get_db
from app.schemas import product_schema
from app.services import product_service
from app.core.security import get_current_active_user
from app.models.user_model import User as UserModel # For type hint
from app.models.product_model import ProductStatusEnum
from .image_upload_util import save_upload_file, remove_file, UPLOAD_DIR # Import utility
from app.core.config import settings # For constructing full image URL


router = APIRouter()


@router.post("/{product_id}/upload-image", response_model=product_schema.ProductRead)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_product = product_service.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Remove old image if it exists
    if db_product.image_url:
        remove_file(db_product.image_url)
        db_product.image_url = None # Clear it before saving new one

    relative_file_path = save_upload_file(upload_file=file)

    # Update product with new image_url
    updated_product_data = product_schema.ProductUpdate(image_url=relative_file_path)

    # Use the existing update service but ensure it can handle image_url correctly
    # The service needs to be aware not to overwrite other fields if only image_url is passed.
    # A specific service function might be cleaner if update_product is complex.
    updated_db_product = product_service.update_product(db=db, db_product=db_product, product_in=updated_product_data)

    # The ProductRead schema should ideally transform relative image_url to full URL
    # This is handled by get_product_with_full_image_url in product_service or a property in schema
    return updated_db_product


@router.get("/{product_id}/price-tag", response_model=product_schema.PriceTagData)
def get_product_price_tag_data(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Or allow anonymous if tags are public
):
    db_product = product_service.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return product_schema.PriceTagData(
        product_name=db_product.name,
        sku=db_product.sku,
        selling_price=db_product.selling_price
    )

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
