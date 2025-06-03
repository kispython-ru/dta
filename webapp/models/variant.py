from webapp.database import Base
from webapp.database.sqlalchemy.mixins import IDMixin


class Variant(Base, IDMixin):
    __tablename__ = "variants"
