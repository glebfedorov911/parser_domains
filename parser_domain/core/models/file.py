from sqlalchemy.orm import Mapped, mapped_column, declared_attr, DeclarativeBase, relationship
from sqlalchemy import String, ForeignKey

from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .statistic import Statistic
    from .showdata import ShowData


class File(Base):
    file: Mapped[str] = mapped_column(nullable=False)
    statistic: Mapped[list["Statistic"]] = relationship(back_populates="file") 
    showdata: Mapped[list["ShowData"]] = relationship(back_populates="file") 