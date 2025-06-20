from fastapi import FastAPI
from app.core.config import settings
from app.apis import (
    auth_router,
    tax_rate_router,
    supplier_router,
    product_category_router,
    product_router,
    sale_router,
    payout_router,
    shelf_router,
    rental_contract_router,
    rental_invoice_router,
    report_router,
    import_router # Added now
)
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Ensure the static directory exists, similar to image_upload_util
static_dir = Path("static")
static_dir.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include routers
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(tax_rate_router.router, prefix=f"{settings.API_V1_STR}/tax-rates", tags=["Tax Rates"])
app.include_router(supplier_router.router, prefix=f"{settings.API_V1_STR}/suppliers", tags=["Suppliers"])
app.include_router(product_category_router.router, prefix=f"{settings.API_V1_STR}/product-categories", tags=["Product Categories"])
app.include_router(product_router.router, prefix=f"{settings.API_V1_STR}/products", tags=["Products"])
app.include_router(sale_router.router, prefix=f"{settings.API_V1_STR}/sales", tags=["Sales"])
app.include_router(payout_router.router, prefix=f"{settings.API_V1_STR}/payouts", tags=["Payouts"])
app.include_router(shelf_router.router, prefix=f"{settings.API_V1_STR}/shelves", tags=["Shelves"])
app.include_router(rental_contract_router.router, prefix=f"{settings.API_V1_STR}/rental-contracts", tags=["Rental Contracts"])
app.include_router(rental_invoice_router.router, prefix=f"{settings.API_V1_STR}/rental-invoices", tags=["Rental Invoices"])
app.include_router(report_router.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(import_router.router, prefix=f"{settings.API_V1_STR}/import", tags=["Data Import"])


# Mount static files directory for serving product images
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

# Optional: Add a command to create initial roles and admin user if they don't exist.
# This could be a separate script or a CLI command using Typer.
# For now, this is a manual step or can be handled by Alembic data migrations.

# @app.on_event("startup")
# async def startup_event():
#     # This is a potential place to create initial data, but alembic data migrations are better.
#     # from app.db.session import SessionLocal
#     # from app.services import user_service # Corrected import
#     # from app.schemas.user_schema import UserCreate # RoleCreate not used here directly
#     # from app.models import user_model # to ensure tables are created if not using alembic for it
#     # from app.db.session import engine
#     # # user_model.Base.metadata.create_all(bind=engine) # Not recommended for production, use Alembic
#     # db = SessionLocal()
#     # try:
#     #     admin_role = user_service.get_or_create_role(db, "Admin", "Administrator role with full access")
#     #     employee_role = user_service.get_or_create_role(db, "Mitarbeiter", "Employee role with operational access")
#     #     # Create a default admin user if none exists
#     #     admin_user = user_service.get_user_by_email(db, email="admin@example.com") # Pass email as keyword arg
#     #     if not admin_user:
#     #         user_in = UserCreate(
#     #             email="admin@example.com",
#     #             password="adminpassword", # Change this in a real setup!
#     #             full_name="Admin User",
#     #             role_id=admin_role.id,
#     #             is_active=True
#     #         )
#     #         user_service.create_user(db, user=user_in) # Pass user as keyword arg
#     # finally:
#     #     db.close()
#     pass
