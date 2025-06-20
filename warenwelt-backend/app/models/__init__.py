# This file will import all models so Base has them registered.
from .user_model import User, Role
from .tax_rate_model import TaxRate
from .supplier_model import Supplier
from .product_category_model import ProductCategory
from .product_model import Product
from .sale_model import Sale, SaleItem
from .payout_model import Payout # Added Payout
from .shelf_model import Shelf
from .rental_contract_model import RentalContract
from .rental_invoice_model import RentalInvoice


# Ensure Base is accessible for alembic and all models are registered with it
from app.db.session import Base
