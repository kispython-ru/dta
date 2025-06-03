from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class Student(Base, IDMixin):
    __tablename__ = "students"

    external_id: Mapped[int | None] = mapped_column(BigInteger)
    provider: Mapped[str | None]
    email: Mapped[str]
    group: Mapped[str | None]
    variant: Mapped[int | None]
    password_hash: Mapped[str | None]
    unconfirmed_hash: Mapped[str | None]
    blocked: Mapped[bool]
    teacher: Mapped[bool | None]
