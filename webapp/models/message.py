from datetime import datetime
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class Message(Base, IDMixin):
    __tablename__ = "messages"

    task: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    variant: Mapped[int] = mapped_column(ForeignKey("variants.id"))
    group: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    time: Mapped[datetime] = mapped_column(default=func.now())
    code: Mapped[str]
    ip: Mapped[str]
    session_id: Mapped[str | None]
    processed: Mapped[bool]
    student: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
