from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from webapp.database import Base
from ..enums import Status


class TaskStatus(Base):
    __tablename__ = "task_statuses"

    task: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    variant: Mapped[int] = mapped_column(
        ForeignKey("variants.id"), primary_key=True)
    group: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime)
    code: Mapped[str]
    ip: Mapped[str]
    output: Mapped[str | None]
    status: Mapped[Status]
    achievements: Mapped[list | None]
