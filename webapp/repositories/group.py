from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.group import Group as Model


class GroupRepository(BaseRepository, IDRepositoryMixin):
    model = Model

    def get_by_prefix(self, prefix: str) -> list[Model]:
        return self.get_many(self.model.title.startswith(prefix))

    def rename(self, group_id: int, title: str) -> None:
        self.update_one(group_id, {"title": title})

    def create_by_names(self, names: list[str]) -> list[Model]:
        return [self.create(name=name) for name in names]

    def create(self, name: str) -> Model:
        return self.add_n_return(data={"title": name})
