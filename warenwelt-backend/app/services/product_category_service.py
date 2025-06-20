from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.product_category_model import ProductCategory
from app.schemas.product_category_schema import ProductCategoryCreate, ProductCategoryUpdate

def get_product_category(db: Session, category_id: int) -> Optional[ProductCategory]:
    return db.query(ProductCategory).filter(ProductCategory.id == category_id).first()

def get_product_category_by_name(db: Session, name: str) -> Optional[ProductCategory]:
    return db.query(ProductCategory).filter(ProductCategory.name == name).first()

def get_product_categories(db: Session, skip: int = 0, limit: int = 100) -> List[ProductCategory]:
    return db.query(ProductCategory).offset(skip).limit(limit).all()

def create_product_category(db: Session, category: ProductCategoryCreate) -> ProductCategory:
    db_category = ProductCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_product_category(
    db: Session, db_category: ProductCategory, category_in: ProductCategoryUpdate
) -> ProductCategory:
    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_product_category(db: Session, category_id: int) -> Optional[ProductCategory]:
    db_category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    if db_category:
        # Add logic here to check if category can be deleted (e.g., no associated products)
        # For MVP, we allow direct deletion.
        # if db_category.products: # Assuming 'products' relationship exists
        #     raise ValueError("Category has associated products and cannot be deleted.")
        db.delete(db_category)
        db.commit()
    return db_category
