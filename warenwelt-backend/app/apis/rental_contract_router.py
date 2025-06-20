from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel # For local DeleteSuccessMessageContract

from app.db.session import get_db
from app.schemas import rental_contract_schema # Imports all from rental_contract_schema
from app.models.rental_contract_model import RentalContractStatusEnum # For query param enum
from app.services import rental_contract_service
from app.models.user_model import User as UserModel # For dependency injection
from app.core.security import get_current_active_user # For user authentication/authorization

# Define a response model for delete operations if returning a custom message for contracts
class DeleteSuccessMessageContract(BaseModel):
    id: int
    contract_number: Optional[str] = None
    message: str

router = APIRouter()

@router.post(
    "/",
    response_model=rental_contract_schema.RentalContractRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rental contract",
    description="Creates a new rental contract, linking a shelf to a tenant (supplier) for a specific period and price."
)
def create_new_rental_contract(
    contract_in: rental_contract_schema.RentalContractCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    """
    Create a new rental contract.
    - **shelf_id**: ID of the shelf to be rented.
    - **tenant_supplier_id**: ID of the supplier acting as the tenant.
    - **start_date**, **end_date**: Rental period.
    - **rent_price_at_signing**: Agreed rental price.
    - **contract_number**: Optional, will be auto-generated if not provided.
    """
    return rental_contract_service.create_rental_contract(db=db, contract_in=contract_in)

@router.get(
    "/{contract_id}",
    response_model=rental_contract_schema.RentalContractRead,
    summary="Get a single rental contract by ID"
)
def read_single_rental_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_contract = rental_contract_service.get_rental_contract(db, contract_id=contract_id)
    if db_contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental contract not found")
    return db_contract

@router.get(
    "/",
    response_model=List[rental_contract_schema.RentalContractRead],
    summary="List rental contracts with optional filters"
)
def read_rental_contracts_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records"),
    shelf_id: Optional[int] = Query(None, description="Filter by shelf ID"),
    tenant_supplier_id: Optional[int] = Query(None, description="Filter by tenant (supplier) ID"),
    contract_status: Optional[RentalContractStatusEnum] = Query(None, description="Filter by contract status (e.g., ACTIVE, PENDING)"),
    start_date_from: Optional[date] = Query(None, description="Filter: contract start date is on or after this date (YYYY-MM-DD)"),
    start_date_to: Optional[date] = Query(None, description="Filter: contract start date is on or before this date (YYYY-MM-DD)"),
    end_date_from: Optional[date] = Query(None, description="Filter: contract end date is on or after this date (YYYY-MM-DD)"),
    end_date_to: Optional[date] = Query(None, description="Filter: contract end date is on or before this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    contracts = rental_contract_service.get_rental_contracts(
        db,
        skip=skip,
        limit=limit,
        shelf_id=shelf_id,
        tenant_supplier_id=tenant_supplier_id,
        contract_status=contract_status,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        end_date_from=end_date_from,
        end_date_to=end_date_to
    )
    return contracts

@router.put(
    "/{contract_id}",
    response_model=rental_contract_schema.RentalContractRead,
    summary="Update an existing rental contract"
)
def update_existing_rental_contract(
    contract_id: int,
    contract_in: rental_contract_schema.RentalContractUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    # The service layer (update_rental_contract) now raises HTTPException for 404.
    updated_contract = rental_contract_service.update_rental_contract(
        db=db, contract_id=contract_id, contract_in=contract_in
    )
    return updated_contract

@router.delete(
    "/{contract_id}",
    response_model=DeleteSuccessMessageContract, # Using the specific delete message model
    summary="Delete a rental contract"
)
def remove_rental_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    # The service layer (delete_rental_contract) now raises 404 if not found,
    # and returns a dict that matches DeleteSuccessMessageContract.
    delete_info = rental_contract_service.delete_rental_contract(db=db, contract_id=contract_id)
    return delete_info
