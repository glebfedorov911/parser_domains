# class DateModel(models.Model):
#     date = models.CharField(max_length=21, null=False, blank=True)

from sqlalchemy.orm import Mapped, mapped_column, declared_attr, DeclarativeBase, relationship
from sqlalchemy import String, ForeignKey

from typing import TYPE_CHECKING

from .base import Base

class Date(Base):
    date: Mapped[str] = mapped_column(nullable=False)