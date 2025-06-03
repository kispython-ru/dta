from datetime import datetime
from typing import Any
from sqlalchemy import delete, select, func, update

from webapp.database import BaseRepository
from webapp.models.task_status import TaskStatus as Model
from webapp.models.group import Group
from webapp.enums import Status


class TaskStatusRepository(BaseRepository):

    model = Model

    STATUS_CHECKED = [
        Status.Checked,
        Status.CheckedFailed,
        Status.CheckedSubmitted
    ]

    def update_one(
            self, task: int, variant: int, group: int, data: dict[str, Any]
    ) -> Model:
        stmt = (
            update(self.model)
            .filter_by(task=task, variant=variant, group=group)
            .values(**data)
            .returning(self.model)
        )
        return self.execute(stmt).scalar_one_or_none()

    def delete_one(self, group: int) -> None:
        stmt = delete(self.model).filter_by(group=group)
        self.execute(stmt)

    def get_by_group(self, group: int) -> list[Model]:
        return self.get_many(group=group)

    def get_group_rating(self) -> list[tuple[Model, int]]:
        # TODO move it to GroupRepository with relationships features
        stmt = select(
            Group,
            func.count(Group.id).label('score')
        ).join(
            self.model,
            Group.id == self.model.group
        ).where(
            self.model.status.in_(self.STATUS_CHECKED)
        ).group_by(Group.id)
        return self.execute(stmt).tuples().all()

    def get_rating(self) -> list[tuple[Group, Model]]:
        stmt = select(Group, self.model).join(
            self.model,
            Group.id == self.model.group
        ).where(
            self.model.status.in_(self.STATUS_CHECKED)
        )
        return self.execute(stmt).tuples().all()

    def get_task_status(
            self, task: int, variant: int, group: int
    ) -> Model | None:
        return self.get_one(
            task=task,
            variant=variant,
            group=group
        )

    def delete_group_task_statuses(self, group: int) -> None:
        statuses = self.get_many(group=group)
        for status in statuses:
            self.delete_one(group)

    def record_achievement(
            self, task: int, variant: int, group: int, achievement: int
    ) -> None:
        status = self.get_task_status(task, variant, group)
        if status:
            achievements = list(set(status.achievements + [achievement]))
            self.update_one(*(task, variant, group),
                            {"achievements": achievements})

    def clear_achievements(self) -> None:
        stmt = (
            update(self.model)
            .where(self.model.achievements.isnot(None))
            .values({"achievements": None})
        )
        self.execute(stmt)

    def check(
            self,
            task: int,
            variant: int,
            group: int,
            code: str,
            ok: bool,
            output: str,
            ip: str
    ) -> Model:
        if ok:
            new_status = Status.Checked
        else:
            task_status = self.get_task_status(task, variant, group)
            new_status = (
                Status.CheckedFailed
                if task_status and task_status.status in self.STATUS_CHECKED
                else Status.Failed
            )
        return self.create_or_update(
            task, variant, group, code, new_status, output, ip
        )

    def submit_task(
            self, task: int, variant: int, group: int, code: str, ip: str
    ) -> Model:
        task_status = self.get_task_status(task, variant, group)
        new_status = (
            Status.CheckedSubmitted
            if task_status and task_status.status in self.STATUS_CHECKED
            else Status.Submitted
        )
        return self.create_or_update(
            task, variant, group, code, new_status, None, ip
        )

    def create_or_update(
            self,
            task: int,
            variant: int,
            group: int,
            code: str,
            status: int,
            output: str,
            ip: str
    ) -> Model:
        data = {
            "code": code,
            "time": datetime.now(),
            "status": status,
            "output": output,
            "ip": ip
        }
        task_status = self.update_one(*(task, variant, group), data)
        data.update({"task": task, "variant": variant, "group": group})
        return task_status or self.add_n_return(data)
