from sqlalchemy.orm import Session

from app import crud
from app.models.user import User
from app.schemas.article import ArticleCreate
from app.tests.utils.user import random_lower_string


def create_random_article(db: Session, owner_id: int):
    name = random_lower_string()
    description = random_lower_string()
    price = 10.5
    article_in = ArticleCreate(name=name, description=description, price=price)
    return crud.article.create_with_owner(db=db, obj_in=article_in, owner_id=owner_id)
