from sqlalchemy import Column, Integer, String
from app.utils import Base


class User(Base):
    __tablename__ = 'users'
    id = Column("id", Integer, primary_key=True, nullable=False)
    email = Column("email", String, unique=True, nullable=False)
    password = Column("password", String, nullable=False)
