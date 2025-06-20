from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta, datetime # datetime needed for some schema fields

from app.db.session import get_db
from app.schemas import report_schema as ReportSchema # Alias for clarity
from app.services import report_service # New report service
from app.models.user_model import User as UserModel # For dependency injection
from app.core.security import get_current_active_user # For user authentication/authorization
from fastapi.responses import StreamingResponse # For CSV export
import io # For StreamingResponse with string content

router = APIRouter()

# TODO: Implement robust permission checks for all report endpoints.
# Example:
# from app.core.permissions import check_role
# @router.get("/some_report", dependencies=[Depends(check_role(["Admin", "Manager"]))])

@router.get(
    "/sales/summary/daily",
    response_model=ReportSchema.DailySummaryReport,
    summary="Get a daily sales summary report",
    description="Provides a summary of sales for a specific day, including total amounts and breakdowns by payment method."
)
def get_daily_summary(
    report_date: date = Query(..., description="Date for the report in YYYY-MM-DD format. Example: 2024-07-28"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        summary_report = report_service.get_daily_sales_summary(db, report_date=report_date)
        return summary_report
    except ValueError as ve: # Catch specific errors from service if any
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log error e (import logging and use logging.error(f"Error: {e}", exc_info=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate daily summary: {str(e)}")


@router.get(
    "/sales/summary/weekly",
    response_model=ReportSchema.PeriodSummaryReport,
    summary="Get a weekly sales summary report",
    description="Provides a sales summary for a full week (Monday to Sunday). Specify any date within the desired week; the service will calculate the week's boundaries."
)
def get_weekly_summary(
    # To define a week, it's often easier for the client to provide any date within that week.
    # The backend then calculates the actual start (Monday) and end (Sunday) of that week.
    # Or, require a specific start_date (Monday) as initially planned.
    target_date_for_week: date = Query(..., description="A date within the desired week (YYYY-MM-DD). The report will cover Monday to Sunday of this week."),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        # Calculate start (Monday) and end (Sunday) of the week containing target_date_for_week
        start_of_week = target_date_for_week - timedelta(days=target_date_for_week.weekday()) # Monday
        end_of_week = start_of_week + timedelta(days=6) # Sunday

        summary_report = report_service.get_period_sales_summary(
            db, start_date=start_of_week, end_date=end_of_week, report_type="WEEKLY"
        )
        return summary_report
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate weekly summary: {str(e)}")


@router.get(
    "/sales/summary/monthly",
    response_model=ReportSchema.PeriodSummaryReport,
    summary="Get a monthly sales summary report",
    description="Provides a sales summary for a specific calendar month."
)
def get_monthly_summary(
    year: int = Query(..., ge=2000, le=datetime.now().year + 5, description="Year for the report (e.g., 2024)"),
    month: int = Query(..., ge=1, le=12, description="Month for the report (1-12)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        month_start_date = date(year, month, 1)
        # Calculate end_date for the month robustly
        if month == 12:
            month_end_date = date(year, month, 31)
        else:
            month_end_date = date(year, month + 1, 1) - timedelta(days=1)

        summary_report = report_service.get_period_sales_summary(
            db, start_date=month_start_date, end_date=month_end_date, report_type="MONTHLY"
        )
        return summary_report
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid year/month provided: {str(ve)}")
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate monthly summary: {str(e)}")

@router.get(
    "/revenue/list",
    response_model=ReportSchema.RevenueListReport,
    summary="Get a detailed list of revenue items for a period",
    description="Provides a detailed breakdown of all items sold within a specified period, including product type and pricing information. Useful for deeper sales analysis."
)
def get_revenue_list(
    start_date: date = Query(..., description="Start date for the report period (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for the report period (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date.")

    # Optional: Add a limit to the date range to prevent very large reports if necessary
    # max_days_limit = 90
    # if (end_date - start_date).days > max_days_limit:
    #     raise HTTPException(status_code=400, detail=f"Date range too large, maximum {max_days_limit} days allowed.")

    try:
        report = report_service.get_revenue_list_report(db, start_date=start_date, end_date=end_date)
        return report
    except ValueError as ve: # Catch specific errors from service if any
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log error e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate revenue list report: {str(e)}")


# --- CSV Export Endpoints ---

@router.get(
    "/export/daily-sales-summary/csv",
    summary="Export daily sales summary as CSV",
    description="Downloads a CSV file containing the daily sales summary for the specified date.",
    response_class=StreamingResponse
)
async def export_daily_summary_csv_endpoint(
    report_date: date = Query(..., description="Date for the report (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # TODO: Add specific permission check
    try:
        csv_content = report_service.export_daily_sales_summary_csv(db, report_date_in=report_date)
        file_name = f"tageslosung_{report_date.strftime('%Y-%m-%d')}.csv"

        # For DATEV, encoding 'cp1252' (Windows Latin 1) is often preferred over 'utf-8'.
        # Check DATEV specifications for the required encoding.
        # For this example, using utf-8 as a general default.
        response = StreamingResponse(
            iter([csv_content.encode('utf-8')]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"{file_name}\""} # Ensure filename is quoted
        )
        return response
    except Exception as e:
        # Log error (e.g., logging.error(f"CSV Export Error: {e}", exc_info=True))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export daily sales summary CSV: {str(e)}")

@router.get(
    "/export/monthly-sales-summary/csv",
    summary="Export monthly sales summary as CSV",
    description="Downloads a CSV file containing the monthly sales summary for the specified year and month.",
    response_class=StreamingResponse
)
async def export_monthly_summary_csv_endpoint(
    year: int = Query(..., ge=2000, le=datetime.now().year + 5, description="Year for the report"),
    month: int = Query(..., ge=1, le=12, description="Month for the report (1-12)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # TODO: Add specific permission check
    try:
        csv_content = report_service.export_monthly_sales_summary_csv(db, year=year, month=month)
        file_name = f"monatslosung_{year}-{month:02d}.csv"

        response = StreamingResponse(
            iter([csv_content.encode('utf-8')]), # Consider 'cp1252' for DATEV compatibility
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"{file_name}\""}
        )
        return response
    except Exception as e:
        # Log error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export monthly sales summary CSV: {str(e)}")

@router.get(
    "/export/revenue-list/datev-like/csv",
    summary="Export revenue list in a DATEV-like CSV format (simplified)",
    description="Downloads a CSV file containing a list of revenue items, structured similarly to a DATEV import format. This is a simplified version and may need adjustment for specific DATEV requirements.",
    response_class=StreamingResponse
)
async def export_revenue_list_datev_endpoint(
    start_date: date = Query(..., description="Start date for the period (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for the period (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # TODO: Add specific permission check
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date.")
    try:
        csv_content = report_service.export_revenue_list_datev_like_csv(db, start_date_in=start_date, end_date_in=end_date)
        file_name = f"buchungsstapel_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.csv"

        response = StreamingResponse(
            iter([csv_content.encode('utf-8')]), # DATEV often prefers 'cp1252'
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"{file_name}\""}
        )
        return response
    except Exception as e:
        # Log error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export DATEV-like revenue list CSV: {str(e)}")
