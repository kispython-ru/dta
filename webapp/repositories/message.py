from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.sql import func

from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.message import Message as Model


class MessageRepository(BaseRepository, IDRepositoryMixin):

    model = Model

    def submit_task(
        self,
        task: int,
        variant: int,
        group: int,
        code: str,
        ip: str,
        student: int | None = None,
        session_id: str | None = None
    ) -> Model:
        return self.add_n_return(data={
            "processed": False,
            "time": datetime.now(),
            "task": task,
            "variant": variant,
            "group": group,
            "code": code,
            "ip": ip,
            "student": student,
            "session_id": session_id
        })

    def get_latest(self, count: int) -> list[Model]:
        return self.get_many(
            limit_=count, order_by_=[desc(self.model.time)]
        )

    def get_pending_messages(self) -> list[Model]:
        return self.get_many(
            processed=False, order_by_=[self.model.time.asc()]
        )

    def get_student_variants(
            self, student: int, group: int
    ) -> list[int]:
        # TODO maybe upgrade get_many by adding group_by arg and using it here
        stmt = select(self.model.variant).where(
            self.model.student == student, self.model.group == group
        ).group_by(self.model.variant).order_by(desc(func.count()))
        return (self.execute(stmt)).scalars().all()

    def get_next_pending_message(self) -> Model | None:
        return (self.get_many(
            limit_=1,
            order_by_=[self.model.time],
            processed=False
        ))[0]

    def get(self, task: int, variant: int, group: int) -> list[Model]:
        return self.get_many(
            task=task,
            variant=variant,
            group=group,
            order_by_=[desc(self.model.time)]
        )

    def mark_as_processed(self, message_id: int) -> None:
        self.update_one(message_id, {"processed": True})

    def get_all(self):
        return self.get_many(order_by_=[desc(self.model.time)])
