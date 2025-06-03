from datetime import datetime
from sqlalchemy import null, select, desc, func

from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.message_check import MessageCheck as Model
from webapp.models.message import Message
from webapp.models.student import Student
from webapp.enums import Status


class MessageCheckRepository(BaseRepository, IDRepositoryMixin):

    model = Model

    def get(self, message: int) -> Model:
        # TODO make normal arguments naming
        return self.get_by_id(message)

    def checked(self) -> list[Model]:
        return self.get_many(status=Status.Checked)

    def get_by_student(
            self, student: Student, skip: int, take: int
    ) -> list[tuple[Model, Message]]:
        # TODO implement relationships, uncomment this code:
        # return self.get_many(
        #     student=student.id,
        #     offset_=skip,
        #     limit_=take,
        #     order_by_=[desc(Message.time)],
        #     options_=(joinedload(MessageCheck.message),)
        # )
        stmt = select(Model, Message).join(
            Message,
            Message.id == Model.message
        ).where(
            Message.student == student.id
        ).order_by(
            desc(Message.time)
        ).offset(skip).limit(take)
        return self.execute(stmt).tuples().all()

    def get_by_session_id(
            self, session_id: str, skip: int, take: int
    ) -> list[tuple[Model, Message]]:
        # TODO implement relationships, uncomment this code:
        # return self.get_many(
        #     session_id=session_id,
        #     offset_=skip,
        #     limit_=take,
        #     order_by_=[desc(Message.time)],
        #     options_=(joinedload(MessageCheck.message),)
        # )
        stmt = select(Model, Message).join(
            Message,
            Message.id == Model.message
        ).where(
            Message.session_id == session_id
        ).order_by(
            desc(Message.time)
        ).offset(skip).limit(take)
        return self.execute(stmt).tuples().all()

    def count_student_submissions(self, student: Student) -> int:
        stmt = select(Model).join(
            Message,
            Message.id == Model.message
        ).where(
            Message.student == student.id
        )
        return self.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

    def count_session_id_submissions(self, session_id: str) -> int:
        stmt = select(Model).join(
            Message,
            Message.id == Model.message
        ).where(
            Message.session_id == session_id
        )
        return self.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

    def get_by_task(
            self,
            group: int,
            variant: int,
            task: int,
            skip: int,
            take: int,
            registration: bool
    ) -> list[tuple[Model, Message, Student | None]]:
        # TODO implement relationships
        stmt = select(
            Model, Message, Student if registration else null()
        ).join(
            Message,
            Message.id == Model.message
        )
        if registration:
            stmt = stmt.join(Student, Student.id == Message.student)
        stmt = stmt.where(
            Message.group == group,
            Message.variant == variant,
            Message.task == task
        ).order_by(
            desc(Message.time)
        ).offset(skip).limit(take)
        return self.execute(stmt).tuples().all()

    def count_submissions_by_info(
            self,
            group: int,
            variant: int,
            task: int,
            registration: bool
    ) -> int:
        stmt = select(Model).join(
            Message,
            Message.id == Model.message
        )
        if registration:
            stmt = stmt.join(Student, Student.id == Message.student)
        stmt = stmt.where(
            Message.group == group,
            Message.variant == variant,
            Message.task == task
        )
        return self.execute(
            select(func.count())
            .select_from(stmt.subquery())
        ).scalar()

    def record_achievement(self, check_id: int, achievement: int) -> None:
        self.update_one(check_id, {"achievement": achievement})

    def record_check(
            self, message_id: int, status: int, output: str | None
    ) -> Model:
        return self.add_n_return(data={
            "message": message_id,
            "time": datetime.now(),
            "status": status,
            "output": output
        })
