from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Dict
from datetime import date, timedelta
import uuid # For invoice_number generation if simpler method not used
from decimal import Decimal # For Decimal type hint and operations

from app.models.rental_contract_model import RentalContract, RentalContractStatusEnum
from app.models.rental_invoice_model import RentalInvoice, RentalInvoiceStatusEnum
from app.models.supplier_model import Supplier # Needed for tenant info
from app.models.shelf_model import Shelf # Needed for shelf info
from app.schemas import rental_invoice_schema # Main schema for invoice
from app.core.config import settings # For RENTAL_INVOICE_DUE_DAYS_DEFAULT
from fastapi import HTTPException, status
from sqlalchemy import and_, or_, not_ # For complex queries
from sqlalchemy.exc import IntegrityError # For DB constraint violations
from calendar import monthrange # For getting number of days in month

def _generate_invoice_number(db: Session, for_date: date) -> str:
    """
    Generates a unique invoice number for a rental invoice, e.g., RENT-YYYY-MM-XXXX.
    The sequence XXXX resets monthly.
    """
    month_prefix = for_date.strftime("RENT-%Y-%m")
    # Find the highest existing sequence number for this month
    last_invoice_for_month = db.query(RentalInvoice.invoice_number)\
        .filter(RentalInvoice.invoice_number.like(f"{month_prefix}-%"))\
        .order_by(RentalInvoice.invoice_number.desc())\
        .first()

    sequence_num = 1
    if last_invoice_for_month:
        try:
            sequence_num = int(last_invoice_for_month[0].split('-')[-1]) + 1
        except (ValueError, IndexError):
            # Fallback if parsing fails, though unlikely with controlled format
            # This could happen if manual entries don't follow the pattern
            # Or query all and count if there's risk of non-numeric suffices
            count = db.query(RentalInvoice).filter(RentalInvoice.invoice_number.like(f"{month_prefix}-%")).count()
            sequence_num = count + 1 # Less robust if numbers are skipped

    # Loop to ensure uniqueness in case of race conditions or if sequence_num estimation was off.
    while True:
        new_invoice_number = f"{month_prefix}-{sequence_num:04d}"
        if not db.query(RentalInvoice).filter(RentalInvoice.invoice_number == new_invoice_number).first():
            return new_invoice_number
        sequence_num += 1


def calculate_pro_rata_amount(
    full_month_amount: Decimal,
    contract_period_start_for_month: date,
    contract_period_end_for_month: date,
    actual_month_start: date, # The first day of the month being billed for
    actual_month_end: date     # The last day of the month being billed for
) -> Decimal:
    """
    Calculates pro-rata rental amount for a partial month.
    - full_month_amount: The agreed rent for a full month.
    - contract_period_start_for_month: The day the contract becomes active within this specific month.
    - contract_period_end_for_month: The day the contract ends within this specific month.
    - actual_month_start: The first day of the calendar month (e.g., July 1st).
    - actual_month_end: The last day of the calendar month (e.g., July 31st).
    """
    if contract_period_start_for_month > contract_period_end_for_month:
        return Decimal("0.00") # Invalid period

    days_in_calendar_month = (actual_month_end - actual_month_start).days + 1

    # Number of days the contract is active and billable within the specified period
    billable_days_in_period = (contract_period_end_for_month - contract_period_start_for_month).days + 1

    if billable_days_in_period <= 0 or days_in_calendar_month <= 0:
        return Decimal("0.00")

    # Pro-rata calculation: (Monthly Rent / Days in Calendar Month) * Billable Days
    daily_rate = full_month_amount / Decimal(days_in_calendar_month)
    pro_rata_amount = daily_rate * Decimal(billable_days_in_period)

    return pro_rata_amount.quantize(Decimal("0.01")) # Round to 2 decimal places


def generate_monthly_rental_invoices(db: Session, billing_target_date: Optional[date] = None) -> Dict[str, any]:
    """
    Generates DRAFT rental invoices for all active or relevant pending contracts for the month of billing_target_date.
    If billing_target_date is None, it defaults to the current date (meaning current month).
    This function aims to be idempotent for a given contract and billing period.
    """
    if billing_target_date is None:
        billing_target_date = date.today()

    target_month_start = billing_target_date.replace(day=1)
    _, num_days_in_target_month = monthrange(target_month_start.year, target_month_start.month)
    target_month_end = target_month_start.replace(day=num_days_in_target_month)

    relevant_contracts = db.query(RentalContract).filter(
        RentalContract.start_date <= target_month_end,
        RentalContract.end_date >= target_month_start,
        RentalContract.status.in_([RentalContractStatusEnum.ACTIVE, RentalContractStatusEnum.PENDING])
    ).all()

    generated_invoices_info: List[Dict] = []
    errors_info: List[Dict] = []

    for contract in relevant_contracts:
        # Determine the actual billing period for this contract within the target month
        actual_bill_start_this_month = max(contract.start_date, target_month_start)
        actual_bill_end_this_month = min(contract.end_date, target_month_end)

        if actual_bill_start_this_month > actual_bill_end_this_month:
            continue # Contract does not actually fall into this month part

        # Idempotency check: Has an invoice for this contract and this exact billing period already been created?
        existing_invoice = db.query(RentalInvoice).filter(
            RentalInvoice.rental_contract_id == contract.id,
            RentalInvoice.billing_period_start == actual_bill_start_this_month,
            RentalInvoice.billing_period_end == actual_bill_end_this_month,
            # Optional: also check status not to recreate if already DRAFT/OPEN etc.
            # RentalInvoice.status != RentalInvoiceStatusEnum.CANCELLED
        ).first()

        if existing_invoice:
            errors_info.append({
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "period_start": actual_bill_start_this_month.isoformat(),
                "period_end": actual_bill_end_this_month.isoformat(),
                "reason": f"Invoice already exists (ID: {existing_invoice.id}, Number: {existing_invoice.invoice_number})"
            })
            continue

        amount_for_period = contract.rent_price_at_signing # Assume full month price by default
        # Check if it's a partial month for this contract within the target billing month
        is_full_billing_month_for_contract = (
            contract.start_date <= target_month_start and
            contract.end_date >= target_month_end
        )

        if not is_full_billing_month_for_contract:
            # Pro-rata calculation needed
            amount_for_period = calculate_pro_rata_amount(
                contract.rent_price_at_signing,
                actual_bill_start_this_month,
                actual_bill_end_this_month,
                target_month_start, # Context of the month for days_in_month
                target_month_end
            )

        if amount_for_period <= Decimal("0.00"):
            errors_info.append({
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "reason": "Calculated amount is zero or less, skipping invoice generation."
            })
            continue

        # When to set invoice_date? Today? First of billing month?
        # When to set due_date?
        invoice_issue_date = date.today() # Or target_month_start for consistency
        due_days = getattr(settings, 'RENTAL_INVOICE_DUE_DAYS_DEFAULT', 14) # Get from settings or default
        calculated_due_date = invoice_issue_date + timedelta(days=due_days)

        invoice_data_create = rental_invoice_schema.RentalInvoiceCreate(
            rental_contract_id=contract.id,
            invoice_date=invoice_issue_date,
            due_date=calculated_due_date,
            billing_period_start=actual_bill_start_this_month,
            billing_period_end=actual_bill_end_this_month,
            amount_due=amount_for_period,
            status=RentalInvoiceStatusEnum.DRAFT, # Default to DRAFT
            # invoice_number will be auto-generated by create_rental_invoice if not provided
        )

        try:
            created_invoice = create_rental_invoice(db, invoice_in=invoice_data_create)
            generated_invoices_info.append({
                "invoice_id": created_invoice.id,
                "invoice_number": created_invoice.invoice_number,
                "contract_id": contract.id,
                "amount": created_invoice.amount_due
            })
        except HTTPException as e:
            errors_info.append({
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "reason": f"Failed to create invoice: {e.detail}"
            })
        except Exception as e_gen: # Catch any other unexpected error during creation
            errors_info.append({
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "reason": f"Unexpected error during invoice creation: {str(e_gen)}"
            })


    return {"generated_invoices": generated_invoices_info, "errors": errors_info}


def create_rental_invoice(db: Session, invoice_in: rental_invoice_schema.RentalInvoiceCreate) -> RentalInvoice:
    # Fetch contract to get shelf_id and tenant_supplier_id
    # These are denormalized onto the invoice for easier access.
    contract = db.query(RentalContract).filter(RentalContract.id == invoice_in.rental_contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RentalContract with ID {invoice_in.rental_contract_id} not found.")

    invoice_number_to_use = invoice_in.invoice_number
    if not invoice_number_to_use:
        # Generate based on billing_period_start to ensure monthly sequence
        invoice_number_to_use = _generate_invoice_number(db, invoice_in.billing_period_start)
    else: # Validate uniqueness if provided by user
        if db.query(RentalInvoice).filter(RentalInvoice.invoice_number == invoice_number_to_use).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invoice number '{invoice_number_to_use}' already exists.")

    # Pydantic v1: .dict(), Pydantic v2: .model_dump()
    db_invoice_data = invoice_in.model_dump()
    db_invoice_data['invoice_number'] = invoice_number_to_use
    db_invoice_data['shelf_id'] = contract.shelf_id
    db_invoice_data['tenant_supplier_id'] = contract.tenant_supplier_id

    db_invoice = RentalInvoice(**db_invoice_data)

    try:
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice
    except IntegrityError as e:
        db.rollback()
        # Check for unique constraint on invoice_number again (race condition)
        if "rental_invoices_invoice_number_key" in str(e.orig).lower() or "unique constraint failed: rental_invoices.invoice_number" in str(e.orig).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invoice number '{db_invoice.invoice_number}' conflicts with an existing one (race).")
        # Log e.orig for detailed error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Data integrity issue for invoice: {str(e.orig)}")
    except Exception as e: # Catch any other error
        db.rollback()
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred creating invoice: {str(e)}")

# --- Standard CRUD functions for RentalInvoice ---

def get_rental_invoice(db: Session, invoice_id: int) -> Optional[RentalInvoice]:
    return db.query(RentalInvoice).options(
        selectinload(RentalInvoice.rental_contract).selectinload(RentalContract.shelf), # Load contract then its shelf
        selectinload(RentalInvoice.rental_contract).selectinload(RentalContract.tenant),# Load contract then its tenant
        # Also load direct tenant/shelf from invoice if needed, though contract should have them
        selectinload(RentalInvoice.tenant),
        selectinload(RentalInvoice.shelf)
    ).filter(RentalInvoice.id == invoice_id).first()

def get_rental_invoices(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    rental_contract_id: Optional[int] = None,
    tenant_supplier_id: Optional[int] = None,
    shelf_id: Optional[int] = None,
    status: Optional[RentalInvoiceStatusEnum] = None,
    invoice_date_from: Optional[date] = None,
    invoice_date_to: Optional[date] = None,
    due_date_from: Optional[date] = None,
    due_date_to: Optional[date] = None,
    min_amount_due: Optional[Decimal] = None,
    max_amount_due: Optional[Decimal] = None,
) -> List[RentalInvoice]:
    query = db.query(RentalInvoice).options(
        selectinload(RentalInvoice.tenant), # Eager load tenant for list display
        selectinload(RentalInvoice.shelf)   # Eager load shelf for list display
    ) # Avoid loading full contract for list view for performance, unless specifically needed by frontend list.

    if rental_contract_id is not None:
        query = query.filter(RentalInvoice.rental_contract_id == rental_contract_id)
    if tenant_supplier_id is not None:
        query = query.filter(RentalInvoice.tenant_supplier_id == tenant_supplier_id)
    if shelf_id is not None:
        query = query.filter(RentalInvoice.shelf_id == shelf_id)
    if status:
        query = query.filter(RentalInvoice.status == status)
    if invoice_date_from:
        query = query.filter(RentalInvoice.invoice_date >= invoice_date_from)
    if invoice_date_to:
        query = query.filter(RentalInvoice.invoice_date <= invoice_date_to)
    if due_date_from:
        query = query.filter(RentalInvoice.due_date >= due_date_from)
    if due_date_to:
        query = query.filter(RentalInvoice.due_date <= due_date_to)
    if min_amount_due is not None:
        query = query.filter(RentalInvoice.amount_due >= min_amount_due)
    if max_amount_due is not None:
        query = query.filter(RentalInvoice.amount_due <= max_amount_due)

    return query.order_by(RentalInvoice.invoice_date.desc(), RentalInvoice.id.desc()).offset(skip).limit(limit).all()

def update_rental_invoice(
    db: Session, invoice_id: int, invoice_in: rental_invoice_schema.RentalInvoiceUpdate
) -> Optional[RentalInvoice]:
    db_invoice = get_rental_invoice(db, invoice_id) # Use get_rental_invoice to ensure relations are loaded if needed
    if not db_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental invoice not found")

    update_data = invoice_in.model_dump(exclude_unset=True)

    # Prevent changing key identifiers like rental_contract_id, shelf_id, tenant_supplier_id directly
    # These should only change if the underlying contract is corrected, which is a complex operation.
    # For now, assume they are fixed once invoice is created.
    for key in ['rental_contract_id', 'shelf_id', 'tenant_supplier_id']:
        if key in update_data:
            del update_data[key]

    for key, value in update_data.items():
        setattr(db_invoice, key, value)

    try:
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        # Re-fetch with relationships for the response, as refresh might not populate them all.
        return get_rental_invoice(db, invoice_id) # Ensures consistent response object
    except IntegrityError as e: # e.g. unique constraint on invoice_number if changed
        db.rollback()
        if "rental_invoices_invoice_number_key" in str(e.orig).lower() or "unique constraint failed: rental_invoices.invoice_number" in str(e.orig).lower():
            updated_inv_num = update_data.get("invoice_number", db_invoice.invoice_number)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invoice number '{updated_inv_num}' conflicts with an existing one.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Data integrity issue on update: {str(e.orig)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred updating invoice: {str(e)}")


def delete_rental_invoice(db: Session, invoice_id: int) -> Dict[str, any]:
    db_invoice = get_rental_invoice(db, invoice_id)
    if not db_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental invoice not found")

    # Business logic for deletion: e.g., cannot delete PAID invoices, only DRAFT or CANCELLED?
    # For now, allowing deletion. Consider implications.
    if db_invoice.status == RentalInvoiceStatusEnum.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a PAID invoice. Consider cancelling or archiving.")

    invoice_number_for_msg = db_invoice.invoice_number

    db.delete(db_invoice)
    db.commit()
    return {"id": invoice_id, "invoice_number": invoice_number_for_msg, "message": "Rental invoice deleted successfully"}
