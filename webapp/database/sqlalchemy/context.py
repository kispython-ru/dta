from typing import Callable
from sqlalchemy.orm import Session
from sqlalchemy import Engine, create_engine, text

from .engine import create_session_maker


class DbContext:
    def __init__(self, session: Session):
        self.session = session

    def __enter__(self) -> Session:
        self.session.execute(text("PRAGMA foreign_keys=ON"))
        return self.session

    def __exit__(self, exc_type: type[BaseException] | None, exc_val, trace):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


class DbContextManager:
    engines: dict[str, Engine] = {}

    def __init__(self, get_connection: Callable[[], str]):
        self.get_connection = get_connection

    def get_engine(self, connection_string: str) -> Engine:
        if connection_string not in self.engines:
            self.engines[connection_string] = create_engine(connection_string)
        return self.engines[connection_string]

    def create_session(self) -> DbContext:
        connection_string = self.get_connection()
        self.engine = self.get_engine(connection_string)
        maker = create_session_maker(self.engine)
        session = maker(expire_on_commit=False)
        context = DbContext(session)
        return context
