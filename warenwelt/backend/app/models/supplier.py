from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)

    articles = relationship(
        "Article",
        back_populates="supplier",
        cascade="all, delete-orphan",
    )
