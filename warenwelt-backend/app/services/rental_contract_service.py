from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from datetime import date, datetime # datetime for today
import uuid

from app.models.rental_contract_model import RentalContract, RentalContractStatusEnum
from app.models.shelf_model import Shelf, ShelfStatusEnum
from app.models.supplier_model import Supplier
from app.schemas import rental_contract_schema # Main schema for contract
# from app.schemas import shelf_schema -> Not directly needed here, shelf_service handles shelf schemas
from app.services import shelf_service # To interact with shelf status and validation
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError # For catching DB constraint violations

def _generate_contract_number(db: Session) -> str:
    """Generates a unique contract number for a rental contract."""
    while True:
        # Example: "RC-" + first 8 chars of a UUID
        contract_number = f"RC-{uuid.uuid4().hex[:8].upper()}"
        if not db.query(RentalContract).filter(RentalContract.contract_number == contract_number).first():
            return contract_number

def create_rental_contract(db: Session, contract_in: rental_contract_schema.RentalContractCreate) -> RentalContract:
    # 1. Validate Shelf
    db_shelf = db.query(Shelf).filter(Shelf.id == contract_in.shelf_id).first()
    if not db_shelf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shelf with ID {contract_in.shelf_id} not found.")
    if not db_shelf.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Shelf '{db_shelf.name}' is not active and cannot be part of new contracts.")

    # 2. Validate Tenant (Supplier)
    db_tenant = db.query(Supplier).filter(Supplier.id == contract_in.tenant_supplier_id).first()
    if not db_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant (Supplier) with ID {contract_in.tenant_supplier_id} not found.")

    # 3. Handle Contract Number (Generate if not provided, validate if provided)
    contract_number_to_use = contract_in.contract_number
    if not contract_number_to_use:
        contract_number_to_use = _generate_contract_number(db)
    else: # contract_number was provided, check for uniqueness
        existing_contract_by_number = db.query(RentalContract).filter(RentalContract.contract_number == contract_number_to_use).first()
        if existing_contract_by_number:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Rental contract with number '{contract_number_to_use}' already exists.")

    # 4. Date validation (Pydantic validator should handle basic start < end)
    # More complex overlap validation with existing contracts for the same shelf:
    # This is crucial for production to prevent double-booking a shelf.
    # Query existing ACTIVE or PENDING contracts for this shelf and check for date overlaps.
    # For simplicity in this step, we'll rely on the shelf's current 'AVAILABLE' status for new 'ACTIVE'/'PENDING' contracts.
    if contract_in.status in [RentalContractStatusEnum.ACTIVE, RentalContractStatusEnum.PENDING]:
        if db_shelf.status == ShelfStatusEnum.RENTED:
            # Basic check: if a shelf is RENTED, don't allow another ACTIVE/PENDING contract unless specific rules apply (e.g. future start date)
            # This needs a more robust overlap check based on contract_in.start_date and contract_in.end_date
            # against existing contracts for db_shelf.id
            pass # Placeholder for more advanced overlap logic. For now, we might allow creating PENDING contracts on a RENTED shelf.
        elif db_shelf.status == ShelfStatusEnum.MAINTENANCE:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Shelf '{db_shelf.name}' is under maintenance and cannot be assigned to new active/pending contracts.")
        # If shelf is AVAILABLE, it's generally okay.

    # Create the contract instance
    # Pydantic v1: .dict(), Pydantic v2: .model_dump()
    db_contract_data = contract_in.model_dump()
    db_contract_data['contract_number'] = contract_number_to_use # Ensure generated/validated number is used

    db_contract = RentalContract(**db_contract_data)

    try:
        db.add(db_contract)
        db.flush() # Get ID, check initial constraints

        # Update shelf status if this new contract makes it RENTED
        if db_contract.status == RentalContractStatusEnum.ACTIVE or \
           (db_contract.status == RentalContractStatusEnum.PENDING and db_contract.start_date <= date.today()): # Or more sophisticated logic for PENDING
            if db_shelf.status == ShelfStatusEnum.AVAILABLE:
                db_shelf.status = ShelfStatusEnum.RENTED
                db.add(db_shelf)
            # If db_shelf.status is already RENTED, this implies an overlap or a future contract.
            # The overlap logic mentioned in step 4 should ideally prevent problematic overlaps.

        db.commit()
        db.refresh(db_contract)
        # Eager load related objects for the response using selectinload for collections or joinedload for one-to-one/many-to-one
        return db.query(RentalContract).options(
            selectinload(RentalContract.shelf),
            selectinload(RentalContract.tenant)
        ).filter(RentalContract.id == db_contract.id).first()

    except IntegrityError as e:
        db.rollback()
        # Specific check for contract_number unique constraint if not caught by pre-check (race condition)
        if "rental_contracts_contract_number_key" in str(e.orig).lower() or "unique constraint failed: rental_contracts.contract_number" in str(e.orig).lower():
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Rental contract with number '{db_contract.contract_number}' conflicts with an existing one.")
        # Log e.orig for detailed error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"A data integrity issue occurred: {str(e.orig)}")
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


def get_rental_contract(db: Session, contract_id: int) -> Optional[RentalContract]:
    return db.query(RentalContract).options(
        selectinload(RentalContract.shelf),
        selectinload(RentalContract.tenant) # Assuming 'tenant' is the relationship name to Supplier
    ).filter(RentalContract.id == contract_id).first()

def get_rental_contracts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    shelf_id: Optional[int] = None,
    tenant_supplier_id: Optional[int] = None,
    contract_status: Optional[RentalContractStatusEnum] = None, # Use the enum from model
    start_date_from: Optional[date] = None,
    start_date_to: Optional[date] = None,
    end_date_from: Optional[date] = None,
    end_date_to: Optional[date] = None,
) -> List[RentalContract]:
    query = db.query(RentalContract).options(
        selectinload(RentalContract.shelf),
        selectinload(RentalContract.tenant)
    )
    if shelf_id is not None:
        query = query.filter(RentalContract.shelf_id == shelf_id)
    if tenant_supplier_id is not None:
        query = query.filter(RentalContract.tenant_supplier_id == tenant_supplier_id)
    if contract_status: # Checks if contract_status is not None or empty string
        query = query.filter(RentalContract.status == contract_status)
    if start_date_from:
        query = query.filter(RentalContract.start_date >= start_date_from)
    if start_date_to:
        query = query.filter(RentalContract.start_date <= start_date_to)
    if end_date_from:
        query = query.filter(RentalContract.end_date >= end_date_from)
    if end_date_to:
        query = query.filter(RentalContract.end_date <= end_date_to)

    return query.order_by(RentalContract.start_date.desc(), RentalContract.id.desc()).offset(skip).limit(limit).all()


def update_rental_contract(
    db: Session, contract_id: int, contract_in: rental_contract_schema.RentalContractUpdate
) -> Optional[RentalContract]:
    db_contract = db.query(RentalContract).filter(RentalContract.id == contract_id).first()
    if not db_contract:
        # return None # Or raise HTTPException as per API design
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental contract not found")

    # Pydantic v1: .dict(), Pydantic v2: .model_dump()
    update_data = contract_in.model_dump(exclude_unset=True)

    # Date validation (if both provided in update, or one against existing)
    new_start_date = update_data.get('start_date', db_contract.start_date)
    new_end_date = update_data.get('end_date', db_contract.end_date)
    if new_end_date <= new_start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date must be after start date.")

    original_shelf_id = db_contract.shelf_id
    original_status = db_contract.status
    new_status = update_data.get('status', original_status)
    new_shelf_id = update_data.get('shelf_id', original_shelf_id)

    # Apply updates to the model fields
    for key, value in update_data.items():
        setattr(db_contract, key, value)

    try:
        # Complex logic for shelf status changes based on contract updates
        # 1. If shelf is changed:
        if new_shelf_id != original_shelf_id:
            new_shelf_db = db.query(Shelf).get(new_shelf_id)
            if not new_shelf_db:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"New shelf ID {new_shelf_id} not found.")
            if not new_shelf_db.is_active:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"New shelf '{new_shelf_db.name}' is not active.")

            # If new contract status makes new shelf RENTED
            if new_status in [RentalContractStatusEnum.ACTIVE, RentalContractStatusEnum.PENDING]:
                if new_shelf_db.status == ShelfStatusEnum.AVAILABLE:
                    new_shelf_db.status = ShelfStatusEnum.RENTED
                    db.add(new_shelf_db)
                elif new_shelf_db.status == ShelfStatusEnum.MAINTENANCE:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot assign contract to new shelf '{new_shelf_db.name}' as it's under maintenance.")

            # Old shelf might become available
            old_shelf_db = db.query(Shelf).get(original_shelf_id)
            if shelf_service.can_shelf_be_made_available(old_shelf_db): # Checks if other active/pending contracts exist
                 old_shelf_db.status = ShelfStatusEnum.AVAILABLE
                 db.add(old_shelf_db)

        # 2. If status is changed (on the same shelf or new shelf):
        elif new_status != original_status: # Status changed, shelf_id might be same or different
            current_shelf_db = db.query(Shelf).get(db_contract.shelf_id) # Shelf contract is now associated with
            if new_status in [RentalContractStatusEnum.ACTIVE, RentalContractStatusEnum.PENDING]:
                if current_shelf_db.status == ShelfStatusEnum.AVAILABLE:
                    current_shelf_db.status = ShelfStatusEnum.RENTED
                    db.add(current_shelf_db)
                elif current_shelf_db.status == ShelfStatusEnum.MAINTENANCE:
                     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot set contract to '{new_status.value}' as shelf '{current_shelf_db.name}' is '{current_shelf_db.status.value}'.")
            elif new_status in [RentalContractStatusEnum.EXPIRED, RentalContractStatusEnum.TERMINATED]:
                # If contract becomes inactive, check if the shelf it was on can become available
                if shelf_service.can_shelf_be_made_available(current_shelf_db):
                    current_shelf_db.status = ShelfStatusEnum.AVAILABLE
                    db.add(current_shelf_db)

        # 3. If tenant is changed, validate new tenant
        if 'tenant_supplier_id' in update_data and update_data['tenant_supplier_id'] != db_contract.tenant_supplier_id:
            db_tenant_check = db.query(Supplier).filter(Supplier.id == update_data['tenant_supplier_id']).first()
            if not db_tenant_check:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"New Tenant (Supplier) with ID {update_data['tenant_supplier_id']} not found.")

        db.add(db_contract) # Add contract itself (already in session, but good practice)
        db.commit()
        db.refresh(db_contract)
        return db.query(RentalContract).options(
            selectinload(RentalContract.shelf),
            selectinload(RentalContract.tenant)
        ).filter(RentalContract.id == db_contract.id).first()

    except IntegrityError as e:
        db.rollback()
        if "rental_contracts_contract_number_key" in str(e.orig).lower() or "unique constraint failed: rental_contracts.contract_number" in str(e.orig).lower():
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Rental contract with number '{db_contract.contract_number}' conflicts with an existing one.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"A data integrity issue occurred: {str(e.orig)}")
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


def delete_rental_contract(db: Session, contract_id: int) -> dict:
    db_contract = db.query(RentalContract).options(joinedload(RentalContract.shelf)).filter(RentalContract.id == contract_id).first()
    if not db_contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental contract not found")

    shelf_associated = db_contract.shelf # Shelf before contract deletion
    contract_number_for_message = db_contract.contract_number

    # Delete the contract
    db.delete(db_contract)

    # After deleting the contract, check if the associated shelf should become available
    # This check needs to be done carefully, considering other contracts for the same shelf.
    if shelf_associated:
        # Re-fetch shelf to ensure its state is current before modification
        current_shelf_state = db.query(Shelf).get(shelf_associated.id)
        if shelf_service.can_shelf_be_made_available(current_shelf_state): # This function checks if NO OTHER active/pending contracts exist
            current_shelf_state.status = ShelfStatusEnum.AVAILABLE
            db.add(current_shelf_state)

    db.commit()
    return {"id": contract_id, "contract_number": contract_number_for_message, "message": "Rental contract deleted successfully"}
