from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.schemas.article import Article, ArticleCreate, ArticleUpdate
from app.models.user import User
from app.routes import deps

router = APIRouter()


@router.get("/", response_model=List[Article])
def read_articles(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve articles.
    """
    if crud.user.is_superuser(current_user):
        articles = crud.article.get_multi(db, skip=skip, limit=limit)
    else:
        articles = crud.article.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return articles


@router.post("/", response_model=Article)
def create_article(
    *,
    db: Session = Depends(deps.get_db),
    article_in: ArticleCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new article.
    """
    article = crud.article.create_with_owner(db=db, obj_in=article_in, owner_id=current_user.id)
    return article


@router.put("/{id}", response_model=Article)
def update_article(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    article_in: ArticleUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an article.
    """
    article = crud.article.get(db=db, id=id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not crud.user.is_superuser(current_user) and (article.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    article = crud.article.update(db=db, db_obj=article, obj_in=article_in)
    return article


@router.get("/{id}", response_model=Article)
def read_article(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get article by ID.
    """
    article = crud.article.get(db=db, id=id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not crud.user.is_superuser(current_user) and (article.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return article


@router.delete("/{id}", response_model=Article)
def delete_article(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an article.
    """
    article = crud.article.get(db=db, id=id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not crud.user.is_superuser(current_user) and (article.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    article = crud.article.remove(db=db, id=id)
    return article
