from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid # For SKU generation

from app.models.product_model import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.services import supplier_service, product_category_service, tax_rate_service
from fastapi import HTTPException, status

def _generate_sku(db: Session) -> str:
    """Generates a unique SKU."""
    # Simple SKU: first 3 letters of "PROD" + 8 char UUID hex part
    # Ensure it's unique.
    while True:
        # sku = "PROD-" + uuid.uuid4().hex[:8].upper()
        # Using timestamp and a small random part for more ordered SKUs
        # This is a very basic example, consider more robust/configurable SKU generation for production
        # e.g., based on category, supplier, sequential numbers etc.
        timestamp_part = str(int(uuid.uuid4().int / (10**30)))[:6] # Approx timestamp based part
        random_part = uuid.uuid4().hex[:4].upper()
        sku = f"SKU-{timestamp_part}-{random_part}"
        if not get_product_by_sku(db, sku=sku):
            return sku

def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.supplier),
        joinedload(Product.category),
        joinedload(Product.tax_rate)
    ).filter(Product.id == product_id).first()

def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    return db.query(Product).filter(Product.sku == sku).first()

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None # From ProductStatusEnum
) -> List[Product]:
    query = db.query(Product).options(
        joinedload(Product.supplier),
        joinedload(Product.category),
        joinedload(Product.tax_rate)
    )
    if supplier_id is not None:
        query = query.filter(Product.supplier_id == supplier_id)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if status is not None:
        query = query.filter(Product.status == status)

    return query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()

def create_product(db: Session, product_in: ProductCreate) -> Product:
    # Validate foreign keys
    if not supplier_service.get_supplier(db, product_in.supplier_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with ID {product_in.supplier_id} not found.")
    if not product_category_service.get_product_category(db, product_in.category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID {product_in.category_id} not found.")
    if not tax_rate_service.get_tax_rate(db, product_in.tax_rate_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tax rate with ID {product_in.tax_rate_id} not found.")

    sku = product_in.sku
    if not sku:
        sku = _generate_sku(db)
    elif get_product_by_sku(db, sku=sku):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with SKU '{sku}' already exists.")

    db_product = Product(
        **product_in.model_dump(exclude={"sku"}), # Exclude SKU if it was None, use generated one
        sku=sku
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    # Eager load relationships for the response after creation
    return get_product(db, db_product.id)


def update_product(db: Session, db_product: Product, product_in: ProductUpdate) -> Product:
    update_data = product_in.model_dump(exclude_unset=True)

    # Validate FKs if they are being updated
    if "supplier_id" in update_data and not supplier_service.get_supplier(db, update_data["supplier_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with ID {update_data['supplier_id']} not found.")
    if "category_id" in update_data and not product_category_service.get_product_category(db, update_data["category_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID {update_data['category_id']} not found.")
    if "tax_rate_id" in update_data and not tax_rate_service.get_tax_rate(db, update_data["tax_rate_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tax rate with ID {update_data['tax_rate_id']} not found.")

    # SKU is generally not updatable this way. If SKU update is needed, it should be a special operation.
    if "sku" in update_data and update_data["sku"] != db_product.sku:
         # check if new SKU already exists
        existing_product_sku = get_product_by_sku(db, sku=update_data["sku"])
        if existing_product_sku and existing_product_sku.id != db_product.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with SKU '{update_data['sku']}' already exists.")
        # setattr(db_product, "sku", update_data["sku"]) # Allowing SKU update if provided

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    # Eager load relationships for the response after update
    return get_product(db, db_product.id)


def delete_product(db: Session, product_id: int) -> Optional[Product]:
    db_product = get_product(db, product_id=product_id) # Use get_product to ensure relationships are loaded if needed for checks
    if db_product:
        # Add logic here to check if product can be deleted
        # (e.g., not part of any non-finalized sale, status is appropriate)
        # For MVP, allow direct deletion if status is not 'SOLD' (or similar logic)
        if db_product.status == ProductStatusEnum.SOLD: # Use the enum member
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a product that has been sold.")

        # If product has an image, delete it from filesystem
        if db_product.image_url:
            from app.apis.image_upload_util import remove_file # Import here to avoid circular deps at module level
            remove_file(db_product.image_url)

        db.delete(db_product)
        db.commit()
    return db_product
