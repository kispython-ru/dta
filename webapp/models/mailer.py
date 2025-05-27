from sqlalchemy.orm import Mapped

from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class Mailer(Base, IDMixin):
    __tablename__ = "mailers"

    domain: Mapped[str]
