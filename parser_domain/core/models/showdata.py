from sqlalchemy.orm import Mapped, mapped_column, declared_attr, DeclarativeBase, relationship
from sqlalchemy import String, ForeignKey

from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .file import File


class ShowData(Base):
    domain: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True)
    inn: Mapped[str] = mapped_column(nullable=True)
    ooo: Mapped[str] = mapped_column(nullable=True)
    ip: Mapped[str] = mapped_column(nullable=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=True)
    file = relationship("File", back_populates="showdata")