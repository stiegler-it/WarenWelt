from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict # Dict for batch generation response
from datetime import date
from decimal import Decimal # Required for query param type hint if used, and for response model

from app.db.session import get_db
from app.schemas import rental_invoice_schema # Main schema for invoice operations
from app.models.rental_invoice_model import RentalInvoiceStatusEnum # For query param enum
from app.services import rental_invoice_service
from app.models.user_model import User as UserModel # For dependency injection
from app.core.security import get_current_active_user # For user authentication/authorization
from pydantic import BaseModel # For local response models if needed

# Response model for delete operations, consistent with other routers
class DeleteSuccessMessageInvoice(BaseModel):
    id: int
    invoice_number: Optional[str] = None # Invoice number is a good identifier to return
    message: str

# Response model for the batch generation endpoint
class GenerateInvoicesResponse(BaseModel):
    generated_invoices: List[Dict] # e.g., List of {"invoice_id": int, "invoice_number": str, ...}
    errors: List[Dict] # e.g., List of {"contract_id": int, "reason": str, ...}

router = APIRouter()

@router.post(
    "/generate-monthly/",
    response_model=GenerateInvoicesResponse,
    status_code=status.HTTP_200_OK, # 200 OK as it's a process that reports results, not strictly just resource creation
    summary="Generate monthly rental invoices for a target month",
    description="Triggers the generation of DRAFT invoices for all applicable rental contracts for the specified month. If no date is provided, the current month is used."
)
def trigger_generate_monthly_invoices(
    # Using Body for target_date to make it clear in Swagger UI that it's a payload field for POST.
    # Can also be a Query param if preferred for a POST, but Body is common for parameters controlling actions.
    payload: Optional[dict] = Body(None, example={"billing_target_date": "YYYY-MM-DD"}),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add specific permission check (e.g., Admin or Accountant role)
):
    billing_target_date_val = None
    if payload and 'billing_target_date' in payload and payload['billing_target_date']:
        try:
            billing_target_date_val = date.fromisoformat(payload['billing_target_date'])
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format for billing_target_date. Use YYYY-MM-DD.")

    result = rental_invoice_service.generate_monthly_rental_invoices(db=db, billing_target_date=billing_target_date_val)
    # If the process itself has issues, service layer should raise HTTPException.
    # This response indicates the outcome of the generation process.
    return result

@router.post(
    "/",
    response_model=rental_invoice_schema.RentalInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single rental invoice manually",
    description="Allows for manual creation of a single rental invoice. Tenant and shelf details are derived from the rental_contract_id."
)
def create_new_rental_invoice(
    invoice_in: rental_invoice_schema.RentalInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    return rental_invoice_service.create_rental_invoice(db=db, invoice_in=invoice_in)

@router.get(
    "/{invoice_id}",
    response_model=rental_invoice_schema.RentalInvoiceRead,
    summary="Get a single rental invoice by ID"
)
def read_single_rental_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Basic protection
):
    db_invoice = rental_invoice_service.get_rental_invoice(db, invoice_id=invoice_id)
    if db_invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental invoice not found")
    return db_invoice

@router.get(
    "/",
    response_model=List[rental_invoice_schema.RentalInvoiceRead],
    summary="List rental invoices with optional filters"
)
def read_rental_invoices_list(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return"),
    rental_contract_id: Optional[int] = Query(None, description="Filter by rental contract ID"),
    tenant_supplier_id: Optional[int] = Query(None, description="Filter by tenant (supplier) ID"),
    shelf_id: Optional[int] = Query(None, description="Filter by shelf ID"),
    status: Optional[RentalInvoiceStatusEnum] = Query(None, description="Filter by invoice status"),
    invoice_date_from: Optional[date] = Query(None, description="Filter: invoice date from (YYYY-MM-DD)"),
    invoice_date_to: Optional[date] = Query(None, description="Filter: invoice date to (YYYY-MM-DD)"),
    due_date_from: Optional[date] = Query(None, description="Filter: due date from (YYYY-MM-DD)"),
    due_date_to: Optional[date] = Query(None, description="Filter: due date to (YYYY-MM-DD)"),
    min_amount_due: Optional[Decimal] = Query(None, ge=0, description="Filter: minimum amount due"),
    max_amount_due: Optional[Decimal] = Query(None, ge=0, description="Filter: maximum amount due"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Basic protection
):
    invoices = rental_invoice_service.get_rental_invoices(
        db, skip=skip, limit=limit, rental_contract_id=rental_contract_id,
        tenant_supplier_id=tenant_supplier_id, shelf_id=shelf_id, status=status,
        invoice_date_from=invoice_date_from, invoice_date_to=invoice_date_to,
        due_date_from=due_date_from, due_date_to=due_date_to,
        min_amount_due=min_amount_due, max_amount_due=max_amount_due
    )
    return invoices

@router.put(
    "/{invoice_id}",
    response_model=rental_invoice_schema.RentalInvoiceRead,
    summary="Update an existing rental invoice"
)
def update_existing_rental_invoice(
    invoice_id: int,
    invoice_in: rental_invoice_schema.RentalInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    # The service layer (update_rental_invoice) raises HTTPException for 404 if not found.
    updated_invoice = rental_invoice_service.update_rental_invoice(
        db=db, invoice_id=invoice_id, invoice_in=invoice_in
    )
    return updated_invoice

@router.delete(
    "/{invoice_id}",
    response_model=DeleteSuccessMessageInvoice, # Using the specific delete message model
    summary="Delete a rental invoice"
)
def remove_rental_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    # The service layer (delete_rental_invoice) raises 404 if not found,
    # and 400 if deletion is not allowed (e.g., for PAID invoices).
    # It returns a dict that matches DeleteSuccessMessageInvoice on successful deletion.
    delete_info = rental_invoice_service.delete_rental_invoice(db=db, invoice_id=invoice_id)
    return delete_info
