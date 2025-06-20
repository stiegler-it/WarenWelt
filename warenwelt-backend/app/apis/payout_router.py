from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas import payout_schema
from app.services import payout_service, supplier_service
from app.core.security import get_current_active_user
from app.models.user_model import User as UserModel # For type hint

router = APIRouter()

@router.get("/summary/{supplier_id}", response_model=payout_schema.SupplierPayoutSummary)
def get_supplier_payout_summary_route(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Ensure supplier exists (or let service handle it)
    # supplier = supplier_service.get_supplier(db, supplier_id)
    # if not supplier:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    try:
        summary = payout_service.get_payout_summary_for_supplier(db, supplier_id=supplier_id)
        return summary
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get payout summary: {str(e)}")


@router.post("/", response_model=payout_schema.PayoutRead, status_code=status.HTTP_201_CREATED)
async def create_new_payout( # Changed to async
    payout_in: payout_schema.PayoutCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Permission check: e.g., only Admin or specific finance roles can create payouts
    # if not current_user.role or current_user.role.name not in ["Admin", "Finance"]:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to create payouts.")
    try:
        # Service function is now async
        created_payout = await payout_service.create_payout_for_supplier(db=db, payout_in=payout_in)
        return created_payout
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during payout creation: {str(e)}")


@router.get("/", response_model=List[payout_schema.PayoutRead])
def read_payouts_list(
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Similar permission checks as for sales list might apply
    payouts = payout_service.get_payouts(db, skip=skip, limit=limit, supplier_id=supplier_id)
    return payouts


@router.get("/{payout_id}", response_model=payout_schema.PayoutRead)
def read_single_payout(
    payout_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_payout = payout_service.get_payout(db, payout_id=payout_id)
    if db_payout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout not found")

    # Permission check if necessary (e.g. supplier can only see their own payouts if they had a login)
    # if not (current_user.role.name == "Admin" or (current_user.is_supplier_profile and current_user.supplier_profile.id == db_payout.supplier_id)):
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view this payout.")
    return db_payout
