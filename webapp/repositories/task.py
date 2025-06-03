from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.task import Task as Model


class TaskRepository(BaseRepository, IDRepositoryMixin):

    model = Model

    def get_by_id(self, task_id: int) -> Model | None:
        return super().get_by_id(task_id)

    def create_by_ids(self, ids: list[int]) -> list[Model]:
        return [self.add_n_return(data={"id": task_id}) for task_id in ids]
