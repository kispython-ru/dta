from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class MessageCheck(Base, IDMixin):
    __tablename__ = "message_checks"

    message: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    time: Mapped[datetime]
    status: Mapped[int]
    output: Mapped[str | None]
    achievement: Mapped[int | None]
