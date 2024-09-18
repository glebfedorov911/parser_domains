from sqlalchemy.orm import Mapped, mapped_column, declared_attr, DeclarativeBase, relationship
from sqlalchemy import String, ForeignKey

from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .file import File


class Statistic(Base):
    good: Mapped[int] = mapped_column(nullable=False)
    bad: Mapped[int] = mapped_column(nullable=False)
    check_again: Mapped[int] = mapped_column(nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=True)
    file = relationship("File", back_populates="statistic")