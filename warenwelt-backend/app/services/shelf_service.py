from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.models.shelf_model import Shelf, ShelfStatusEnum
from app.models.rental_contract_model import RentalContract, RentalContractStatusEnum
from app.schemas import shelf_schema # Will import all from shelf_schema
# For RentalContractStatusEnum, it's better to import it directly if used from schemas
# from app.schemas.rental_contract_schema import RentalContractStatusEnum as RentalContractStatusSchemaEnum
# However, the model enum is used in the query for RentalContract.status.in_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

def create_shelf(db: Session, shelf_in: shelf_schema.ShelfCreate) -> Shelf:
    try:
        # Ensure model_dump() is used if Pydantic v2, or .dict() for v1
        db_shelf = Shelf(**shelf_in.model_dump())
        db.add(db_shelf)
        db.commit()
        db.refresh(db_shelf)
        return db_shelf
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Shelf with name '{shelf_in.name}' already exists."
        )
    except Exception as e:
        db.rollback()
        # Consider logging the error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

def get_shelf(db: Session, shelf_id: int) -> Optional[Shelf]:
    return db.query(Shelf).filter(Shelf.id == shelf_id).first()

def get_shelves(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    shelf_status: Optional[ShelfStatusEnum] = None, # Use the model enum for filtering
    is_active: Optional[bool] = None
) -> List[Shelf]:
    query = db.query(Shelf)
    if shelf_status:
        query = query.filter(Shelf.status == shelf_status)
    if is_active is not None: # Check for True or False
        query = query.filter(Shelf.is_active == is_active)

    return query.order_by(Shelf.name).offset(skip).limit(limit).all()

def update_shelf(db: Session, shelf_id: int, shelf_in: shelf_schema.ShelfUpdate) -> Optional[Shelf]:
    db_shelf = get_shelf(db, shelf_id)
    if not db_shelf:
        return None # Or raise HTTPException(status_code=404, detail="Shelf not found")

    # Pydantic v1: update_data = shelf_in.dict(exclude_unset=True)
    # Pydantic v2: update_data = shelf_in.model_dump(exclude_unset=True)
    update_data = shelf_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_shelf, key, value)

    try:
        db.add(db_shelf) # Redundant if db_shelf is already in session and modified
        db.commit()
        db.refresh(db_shelf)
        return db_shelf
    except IntegrityError:
        db.rollback()
        updated_name = update_data.get("name", db_shelf.name)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update shelf. A shelf with name '{updated_name}' may already exist."
        )
    except Exception as e:
        db.rollback()
        # Consider logging the error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while updating shelf: {str(e)}"
        )


def delete_shelf(db: Session, shelf_id: int) -> Optional[Shelf]:
    db_shelf = get_shelf(db, shelf_id)
    if not db_shelf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelf not found")

    # Check for active rental contracts associated with this shelf
    # Using the enum from the rental_contract_model directly
    active_contracts_count = db.query(RentalContract)\
        .filter(RentalContract.shelf_id == shelf_id)\
        .filter(RentalContract.status.in_([
            RentalContractStatusEnum.ACTIVE,
            RentalContractStatusEnum.PENDING
        ])).count()

    if active_contracts_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete shelf '{db_shelf.name}'. It has {active_contracts_count} active or pending rental contract(s). "
                   "Consider deactivating the shelf or terminating associated contracts first."
        )

    # If we reach here, it's safe to delete (hard delete).
    # For soft delete, you would do:
    # db_shelf.is_active = False
    # db.add(db_shelf)
    # db.commit()
    # db.refresh(db_shelf)
    # return db_shelf

    shelf_name_for_message = db_shelf.name # Store before delete for potential message
    db.delete(db_shelf)
    db.commit()
    # After deletion, the object is detached. Can't return it directly if it needs to be accessed by caller.
    # Return a confirmation or the ID, or just None/True. For consistency, can return the (now detached) object.
    # However, it's common to return nothing or a status message upon successful deletion.
    # For now, returning the object for potential use in a confirmation message, but its state is 'deleted'.
    # Let's return a simple dict for confirmation
    return {"id": shelf_id, "name": shelf_name_for_message, "message": "Shelf deleted successfully"}

# Additional helper: Check if shelf can be set to specific statuses
def can_shelf_be_rented(db_shelf: Shelf) -> bool:
    return db_shelf.is_active and db_shelf.status == ShelfStatusEnum.AVAILABLE

def can_shelf_be_made_available(db_shelf: Shelf) -> bool:
    # Check if any active or pending contracts exist for this shelf
    active_or_pending_contracts = db.query(RentalContract)\
        .filter(RentalContract.shelf_id == db_shelf.id)\
        .filter(RentalContract.status.in_([RentalContractStatusEnum.ACTIVE, RentalContractStatusEnum.PENDING]))\
        .count()
    return active_or_pending_contracts == 0
