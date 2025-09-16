from .user import user
from .article import article
from .supplier import supplier

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.article import Article
# from app.schemas.article import ArticleCreate, ArticleUpdate

# article = CRUDBase[Article, ArticleCreate, ArticleUpdate](Article)
