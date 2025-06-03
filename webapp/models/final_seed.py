from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from webapp.database import Base


class FinalSeed(Base):
    __tablename__ = "final_seeds"

    seed: Mapped[str] = mapped_column(unique=True)
    active: Mapped[bool]
    group: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), primary_key=True)
