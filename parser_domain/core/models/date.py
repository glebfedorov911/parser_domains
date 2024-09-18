from sqlalchemy.orm import Mapped, mapped_column, declared_attr, DeclarativeBase, relationship
from sqlalchemy import String, ForeignKey

from typing import TYPE_CHECKING

from .base import Base

class Date(Base):
    date: Mapped[str] = mapped_column(nullable=False)