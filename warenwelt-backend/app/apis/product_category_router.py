from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas import product_category_schema
from app.services import product_category_service
from app.core.security import get_current_active_user
from app.models.user_model import User as UserModel # For type hint

router = APIRouter()

@router.post("/", response_model=product_category_schema.ProductCategoryRead, status_code=status.HTTP_201_CREATED)
def create_new_product_category(
    category_in: product_category_schema.ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    existing_category = product_category_service.get_product_category_by_name(db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product category with name '{category_in.name}' already exists."
        )
    return product_category_service.create_product_category(db=db, category=category_in)


@router.get("/", response_model=List[product_category_schema.ProductCategoryRead])
def read_product_categories_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    categories = product_category_service.get_product_categories(db, skip=skip, limit=limit)
    return categories


@router.get("/{category_id}", response_model=product_category_schema.ProductCategoryRead)
def read_single_product_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_category = product_category_service.get_product_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")
    return db_category


@router.put("/{category_id}", response_model=product_category_schema.ProductCategoryRead)
def update_single_product_category(
    category_id: int,
    category_in: product_category_schema.ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_category = product_category_service.get_product_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")

    if category_in.name and category_in.name != db_category.name:
        existing_category_name = product_category_service.get_product_category_by_name(db, name=category_in.name)
        if existing_category_name and existing_category_name.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product category with name '{category_in.name}' already exists."
            )

    return product_category_service.update_product_category(db=db, db_category=db_category, category_in=category_in)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_single_product_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_category = product_category_service.get_product_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")

    # Add check if category is deletable (e.g. no active products associated)
    # For MVP, direct deletion.
    # if len(db_category.products) > 0: # Assuming products relationship
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete category with active products.")

    product_category_service.delete_product_category(db=db, category_id=category_id)
    return None
