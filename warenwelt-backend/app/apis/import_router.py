from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import Dict, Any, List # Added List

from app.db.session import get_db
from app.services import import_service
from app.models.user_model import User as UserModel # For dependency injection
from app.core.security import get_current_active_user # For user authentication/authorization
from pydantic import BaseModel

router = APIRouter()

class ImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    errors: List[Dict[str, Any]]


@router.post(
    "/suppliers/csv",
    response_model=ImportResponse,
    summary="Import suppliers from a CSV file",
    description=(
        "Upload a CSV file to import suppliers. "
        "Required columns: `supplier_number`. "
        "Optional columns: `company_name`, `first_name`, `last_name`, `email`, `phone`, `is_internal` (true/false). "
        "Delimiter must be semicolon (`;`). Encoding: UTF-8 (recommended) or Latin-1."
    )
)
async def import_suppliers_csv_endpoint( # Renamed for clarity
    csv_file: UploadFile = File(..., description="CSV file with supplier data."),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add specific permission check, e.g., Admin role
):
    if not csv_file.filename or not csv_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Please upload a CSV file.")

    try:
        file_content = await csv_file.read()
        if not file_content:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV file is empty.")
        result = import_service.import_suppliers_from_csv(db, file_content)
        # Consider returning HTTP 207 Multi-Status if there are partial successes and failures.
        # For now, 200 OK and the response body details the outcome.
        return result
    except HTTPException as e: # Re-raise HTTPExceptions from service (e.g., decoding, format)
        raise e
    except Exception as e:
        # Log error e (e.g., logging.error(f"Supplier import error: {e}", exc_info=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during supplier import: {str(e)}")
    finally:
        await csv_file.close()


@router.post(
    "/products/csv",
    response_model=ImportResponse,
    summary="Import products from a CSV file",
    description=(
        "Upload a CSV file to import products. "
        "Required columns: `sku`, `name`, `supplier_number`, `category_name`, `tax_rate_name`, `purchase_price`, `selling_price`, `product_type` (`COMMISSION` or `NEW_WARE`). "
        "Optional columns: `description`, `status` (e.g., `IN_STOCK`, `SOLD`), `entry_date` (YYYY-MM-DD, defaults to today). "
        "Delimiter must be semicolon (`;`). Encoding: UTF-8 (recommended) or Latin-1."
    )
)
async def import_products_csv_endpoint( # Renamed for clarity
    csv_file: UploadFile = File(..., description="CSV file with product data."),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add specific permission check
):
    if not csv_file.filename or not csv_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Please upload a CSV file.")

    try:
        file_content = await csv_file.read()
        if not file_content:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV file is empty.")
        result = import_service.import_products_from_csv(db, file_content)
        return result
    except HTTPException as e: # Re-raise HTTPExceptions from service
        raise e
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during product import: {str(e)}")
    finally:
        await csv_file.close()
