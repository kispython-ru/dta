from sqlalchemy.orm import Mapped

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class AllowedIp(Base, IDMixin):
    __tablename__ = "allowed_ips"

    ip: Mapped[str]
    label: Mapped[str | None]
