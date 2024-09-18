from sqlalchemy.orm import Mapped, mapped_column, declared_attr, DeclarativeBase, relationship
from sqlalchemy import String, ForeignKey

from typing import TYPE_CHECKING

from .base import Base

class DeleteShablon(Base):
    code: Mapped[str] = mapped_column(nullable=False)