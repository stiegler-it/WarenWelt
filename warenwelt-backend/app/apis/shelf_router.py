from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas import shelf_schema # Imports all from shelf_schema
from app.models.shelf_model import ShelfStatusEnum # For query param enum for shelf_status
from app.services import shelf_service
from app.models.user_model import User as UserModel # For dependency injection
from app.core.security import get_current_active_user # For user authentication/authorization

router = APIRouter()

# Define a response model for delete operations if returning a custom message
class DeleteSuccessMessage(shelf_schema.BaseModel): # pydantic.BaseModel
    id: int
    name: Optional[str] = None # Name might not always be available or relevant for all delete messages
    message: str

@router.post(
    "/",
    response_model=shelf_schema.ShelfRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shelf",
    description="Creates a new shelf in the system. Requires appropriate user permissions."
)
def create_new_shelf(
    shelf_in: shelf_schema.ShelfCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check: e.g., if not current_user.role.name in ["Admin", "Manager"]:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
):
    """
    Create a new shelf.
    - **name**: Name of the shelf (must be unique).
    - **monthly_rent_price**: Price for renting the shelf per month.
    - Other fields are optional or have defaults.
    """
    return shelf_service.create_shelf(db=db, shelf_in=shelf_in)

@router.get(
    "/{shelf_id}",
    response_model=shelf_schema.ShelfRead,
    summary="Get a single shelf by ID"
)
def read_single_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect endpoint
):
    db_shelf = shelf_service.get_shelf(db, shelf_id=shelf_id)
    if db_shelf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelf not found")
    return db_shelf

@router.get(
    "/",
    response_model=List[shelf_schema.ShelfRead],
    summary="List all shelves with optional filters"
)
def read_shelves_list(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return"),
    shelf_status: Optional[ShelfStatusEnum] = Query(None, description="Filter by shelf status (e.g., AVAILABLE, RENTED)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true or false)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect endpoint
):
    shelves = shelf_service.get_shelves(
        db, skip=skip, limit=limit, shelf_status=shelf_status, is_active=is_active
    )
    return shelves

@router.put(
    "/{shelf_id}",
    response_model=shelf_schema.ShelfRead,
    summary="Update an existing shelf"
)
def update_existing_shelf(
    shelf_id: int,
    shelf_in: shelf_schema.ShelfUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    updated_shelf = shelf_service.update_shelf(db=db, shelf_id=shelf_id, shelf_in=shelf_in)
    if updated_shelf is None: # Service now raises 404 if not found, so this check might be redundant
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelf not found for update")
    return updated_shelf

@router.delete(
    "/{shelf_id}",
    response_model=DeleteSuccessMessage, # Using a specific response model for delete
    summary="Delete a shelf"
)
def remove_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
    # TODO: Add permission check
):
    # shelf_service.delete_shelf now raises HTTPException for not_found or conflict,
    # and returns a dict like {"id": ..., "name": ..., "message": ...} on success.
    # This dict matches the DeleteSuccessMessage model.
    delete_info = shelf_service.delete_shelf(db=db, shelf_id=shelf_id)
    return delete_info
