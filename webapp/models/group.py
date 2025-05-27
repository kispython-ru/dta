from sqlalchemy.orm import Mapped, mapped_column

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class Group(Base, IDMixin):
    __tablename__ = "groups"

    title: Mapped[str] = mapped_column(unique=True)
    external: Mapped[str | None]
