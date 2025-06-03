from abc import abstractmethod
from typing import Any
from sqlalchemy import Result, delete, exists, select, update

from .models import IDMixin

Model = IDMixin


class IDRepositoryMixin:

    model: type[Model]

    @abstractmethod
    def execute(self, stmt) -> Result:
        raise NotImplementedError

    def _get_with_options(self, id: int, options: tuple) -> Model | None:
        stmt = select(self.model).where(self.model.id == id).options(*options)
        return (self.execute(stmt)).unique().scalar_one_or_none()

    def get_by_id(self, id: int, options: tuple = None) -> Model | None:
        if options:
            return self._get_with_options(id, options)
        stmt = select(self.model).where(self.model.id == id)
        return (self.execute(stmt)).scalar_one()

    def update_one(self, id: int, data: dict[str, Any]) -> Result:
        stmt = update(self.model).where(self.model.id == id).values(**data)
        return self.execute(stmt)

    def update_many(
            self, data: dict[str, dict[str, Any]], options: tuple = ()
    ) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id.in_(data.keys()))
            .values(**data).options(*options)
        )
        return self.execute(stmt, flush=True)

    def exists(self, id: int) -> bool:
        return self.execute(
            select(exists().where(self.model.id == id))
        ).scalar()

    def delete_one(self, id: int) -> None:
        self.execute(delete(self.model).where(self.model.id == id))
