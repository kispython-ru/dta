import enum
from logging import getLogger, Logger
from typing import Any
from typing_extensions import deprecated
from sqlalchemy.types import JSON, DateTime
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy import Result, SQLColumnExpression, delete, func, insert, select

from webapp.enums import Status

from .type_decorators import JsonArray, IntEnum


class Base(DeclarativeBase):

    __abstract__ = True

    type_annotation_map = {
        dict[str, Any]: JSON,
        datetime: DateTime(timezone=True),
        enum.IntEnum: IntEnum(Status),
        list: JsonArray()
    }


Model = Base


class SQLAlchemyRepository:
    model: type[Model]
    logger: Logger

    def __new__(cls, *args: Any, **kwargs: Any) -> "SQLAlchemyRepository":
        if not hasattr(cls, "logger"):
            cls.logger = getLogger(f"SQL.{cls.__name__}")
        return super().__new__(cls)

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session: Session = session

    def execute(self, stmt, flush: bool = False) -> Result:
        self.logger.debug(stmt)
        result: Result = self.session.execute(statement=stmt)
        if flush:
            self.session.flush()
        return result

    def flush(self) -> None:
        self.session.flush()

    def get(self, id: Any) -> Model | None:
        return self.session.get(self.model, id)

    def merge(self, data_orm: Model, flush: bool = False) -> None:
        self.session.merge(data_orm)
        if flush:
            self.session.flush()

    def add_one(self, data: dict[str, Any]) -> int | None:
        stmt = insert(self.model).values(**data)
        return (self.execute(stmt, flush=True)).scalar_one()

    def add_n_return(
            self, data: dict[str, Any], options: tuple = ()
    ) -> Model:
        stmt = (
            insert(self.model)
            .values(**data)
            .returning(self.model)
            .options(*options)
        )
        return (self.execute(stmt, flush=True)).scalar_one()

    def get_many(
            self,
            *criterias: list[SQLColumnExpression],
            offset_: int | None = None,
            limit_: int | None = None,
            options_: tuple = (),
            order_by_: list[SQLColumnExpression] = [],
            **filters: dict[str, Any],
    ) -> list[Model]:
        stmt = (
            select(self.model)
            .where(*criterias)
            .filter_by(**filters)
            .options(*options_)
        )
        if order_by_:
            stmt = stmt.order_by(*order_by_)
        if offset_:
            stmt = stmt.offset(offset_)
        if limit_:
            stmt = stmt.limit(limit_)
        else:
            self.logger.warning(
                f"Using {self.__class__.__name__}.get_many method without "
                + "defining the limit_ parameter can lead to memory overflow"
            )
        result = self.execute(stmt)
        return result.scalars().all()

    def get_one(
            self,
            *criterias: list[SQLColumnExpression],
            _options: list[SQLColumnExpression] = [],
            **filters: dict[str, Any]
    ) -> Model | None:
        stmt = select(self.model).where(
            *criterias).filter_by(**filters).options(*_options)
        return self.execute(stmt).scalar_one_or_none()

    def count(self, *criterias: list[SQLColumnExpression]) -> int:
        stmt = select(func.count()).select_from(self.model)
        if criterias:
            stmt = stmt.where(*criterias)
            return (self.execute(stmt)).scalar_one()

    def get_all(self) -> list[Model]:
        return self.get_many()

    @deprecated("Bro, you are deleting all data from the database. Are you sure you want to do this?")
    def delete_all(self) -> None:
        self.execute(delete(self.model))
