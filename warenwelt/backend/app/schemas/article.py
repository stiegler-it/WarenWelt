from typing import Optional

from pydantic import BaseModel

from .supplier import Supplier
from .user import User

# Shared properties
class ArticleBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    supplier_id: Optional[int] = None


# Properties to receive on article creation
class ArticleCreate(ArticleBase):
    name: str
    price: float


# Properties to receive on article update
class ArticleUpdate(ArticleBase):
    pass


# Properties shared by models stored in DB
class ArticleInDBBase(ArticleBase):
    id: int
    name: str
    owner_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class Article(ArticleInDBBase):
    owner: User
    supplier: Optional[Supplier] = None


# Properties stored in DB
class ArticleInDB(ArticleInDBBase):
    pass
