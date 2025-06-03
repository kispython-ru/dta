from sqlalchemy.orm import Mapped

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class Task(Base, IDMixin):
    __tablename__ = "tasks"

    formulation: Mapped[str | None]
