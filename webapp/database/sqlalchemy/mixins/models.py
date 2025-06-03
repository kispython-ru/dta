from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import declared_attr, Mapped, mapped_column


class TimestampMixin:

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(default=func.now())

    @declared_attr
    def edited_at(cls) -> Mapped[datetime | None]:
        return mapped_column(onupdate=func.now())


class IDMixin:

    @declared_attr
    def id(cls) -> Mapped[int]:
        return mapped_column(primary_key=True, autoincrement=True)
