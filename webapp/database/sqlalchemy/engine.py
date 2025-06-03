from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from .core import Base


def create_session_maker(engine: Engine) -> sessionmaker:
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory
