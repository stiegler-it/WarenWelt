from sqlalchemy.orm import Session

from app import crud
from app.schemas.article import ArticleCreate


class ArticleService:
    def create_article_with_owner(self, db: Session, *, obj_in: ArticleCreate, owner_id: int):
        """
        Create an article with an owner.
        This is a good example of a service method that contains business logic.
        In a real application, this method could do more, e.g. send a notification.
        """
        return crud.article.create_with_owner(db=db, obj_in=obj_in, owner_id=owner_id)


article_service = ArticleService()
