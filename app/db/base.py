# Import all the models, so that Base has them before being
# imported by Alembic
from app.models.base import Base  # noqa
from app.models.user import User  # noqa
from app.models.article import Article  # noqa
from app.models.supplier import Supplier  # noqa
