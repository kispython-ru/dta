import datetime
import uuid
from typing import Callable, List, Union

from sqlalchemy.orm import Session

from webapp.models import (
    FinalSeed,
    Group,
    Message,
    MessageCheck,
    Status,
    Task,
    TaskStatus,
    Variant,
    create_session_maker
)


class DbContext:
    def __init__(self, session: Session):
        self.session = session

    def __enter__(self) -> Session:
        self.session.execute("PRAGMA foreign_keys=ON")
        return self.session

    def __exit__(self, exc_type: type[BaseException] | None, exc_val, trace):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


class DbContextManager:
    def __init__(self, get_connection: Callable[[], str]):
        self.get_connection = get_connection
        self.session_maker = None

    def create_session(self) -> DbContext:
        if self.session_maker is None:
            connection_string = self.get_connection()
            self.session_maker = create_session_maker(connection_string)
        session = self.session_maker(expire_on_commit=False)
        context = DbContext(session)
        return context


class GroupRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_all(self) -> List[Group]:
        with self.db.create_session() as session:
            groups = session.query(Group).all()
            return groups

    def get_by_prefix(self, prefix: str) -> List[Group]:
        with self.db.create_session() as session:
            groups = session.query(Group) \
                .filter(Group.title.startswith(prefix)) \
                .all()
            return groups

    def get_by_id(self, group_id: int) -> Group:
        with self.db.create_session() as session:
            group = session.query(Group).get(group_id)
            return group

    def create_by_names(self, names: List[str]):
        for name in names:
            self.create(name)

    def create(self, name: str) -> Group:
        with self.db.create_session() as session:
            group = Group(title=name)
            session.add(group)
            return group

    def delete_all(self):
        with self.db.create_session() as session:
            session.query(Group).delete()


class TaskRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_all(self) -> List[Task]:
        with self.db.create_session() as session:
            tasks = session.query(Task).all()
            return tasks

    def get_by_id(self, task_id: int) -> Task:
        with self.db.create_session() as session:
            task = session.query(Task).get(task_id)
            return task

    def create_by_ids(self, ids: List[int]):
        with self.db.create_session() as session:
            for task_id in ids:
                group = Task(id=task_id)
                session.add(group)

    def delete_all(self):
        with self.db.create_session() as session:
            session.query(Task).delete()


class VariantRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_all(self) -> List[Variant]:
        with self.db.create_session() as session:
            variants = session.query(Variant).all()
            return variants

    def get_by_id(self, variant_id: int) -> Variant:
        with self.db.create_session() as session:
            variant = session.query(Variant).get(variant_id)
            return variant

    def create_by_ids(self, ids: List[int]):
        with self.db.create_session() as session:
            for variant_id in ids:
                task = Variant(id=variant_id)
                session.add(task)

    def delete_all(self):
        with self.db.create_session() as session:
            session.query(Variant).delete()


class TaskStatusRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_all(self) -> List[TaskStatus]:
        with self.db.create_session() as session:
            statuses = session.query(TaskStatus).all()
            return statuses

    def get_by_group(self, group: int) -> List[TaskStatus]:
        with self.db.create_session() as session:
            statuses = session.query(TaskStatus) \
                .filter_by(group=group) \
                .all()
            return statuses

    def get_task_status(
            self,
            task: int,
            variant: int,
            group: int) -> Union[TaskStatus, None]:
        with self.db.create_session() as session:
            status = session.query(TaskStatus) \
                .filter_by(task=task, variant=variant, group=group) \
                .first()
            return status

    def update_status(
            self,
            task: int,
            variant: int,
            group: int,
            code: str,
            status: int,
            output: str,
            ip: str):
        existing = self.get_task_status(task, variant, group)
        if existing is not None and existing.status == Status.Checked:
            return  # We've already accepted this task!
        with self.db.create_session() as session:
            if existing is not None:
                session.query(TaskStatus) \
                    .filter_by(task=task, variant=variant, group=group) \
                    .update(dict(code=code, status=status, output=output, ip=ip))
                return
            session.add(TaskStatus(
                time=datetime.datetime.now(),
                task=task,
                variant=variant,
                group=group,
                code=code,
                status=status,
                output=output,
                ip=ip,
            ))

    def submit_task(
            self,
            task: int,
            variant: int,
            group: int,
            code: str,
            ip: str) -> TaskStatus:
        with self.db.create_session() as session:
            existing: TaskStatus = session.query(TaskStatus) \
                .filter_by(task=task, variant=variant, group=group) \
                .first()
            if existing is not None:
                if existing.status == Status.Checked:
                    return  # We've already accepted this task!
                session.delete(existing)
            task_status = TaskStatus(
                task=task,
                variant=variant,
                group=group,
                code=code,
                output=None,
                time=datetime.datetime.now(),
                status=Status.Submitted,
                ip=ip,
            )
            session.add(task_status)
            return task_status

    def delete_group_task_statuses(self, group: int):
        with self.db.create_session() as session:
            status = session.query(TaskStatus) \
                .filter_by(group=group) \
                .delete()
            return status


class MessageRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def submit_task(
        self,
        task: int,
        variant: int,
        group: int,
        code: str,
        ip: str
    ) -> Message:
        with self.db.create_session() as session:
            message = Message(
                processed=False,
                time=datetime.datetime.now(),
                task=task,
                variant=variant,
                group=group,
                code=code,
                ip=ip,
            )
            session.add(message)
            return message

    def get_all(self) -> List[Message]:
        with self.db.create_session() as session:
            messages = session.query(Message) \
                .order_by(Message.time.desc()) \
                .all()
            return messages

    def get_latest(self, count: int) -> List[Message]:
        with self.db.create_session() as session:
            latest_messages = session.query(Message) \
                .order_by(Message.time.desc()) \
                .limit(count) \
                .all()
            return latest_messages

    def get_pending_messages(self) -> List[Message]:
        with self.db.create_session() as session:
            pending = session.query(Message) \
                .filter_by(processed=False) \
                .order_by(Message.time.asc()) \
                .all()
            return pending

    def get(self, task: int, variant: int, group: int) -> Union[Message, None]:
        with self.db.create_session() as session:
            return session.query(Message) \
                .filter_by(task=task, variant=variant, group=group) \
                .first()

    def mark_as_processed(self, task: int, variant: int, group: int):
        with self.db.create_session() as session:
            session.query(Message) \
                .filter_by(task=task, variant=variant, group=group) \
                .update(dict(processed=True))


class MessageCheckRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get(self, message: int) -> MessageCheck:
        with self.db.create_session() as session:
            return session.query(MessageCheck) \
                .filter_by(message=message) \
                .first()

    def record_check(
        self,
        message: int,
        status: TaskStatus,
        output: Union[str, None]
    ) -> MessageCheck:
        with self.db.create_session() as session:
            check = MessageCheck(
                time=datetime.datetime.now(),
                message=message,
                status=status,
                output=output,
            )
            session.add(check)
            return check


class FinalSeedRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_final_seed(self, group: int) -> Union[FinalSeed, None]:
        with self.db.create_session() as session:
            return session.query(FinalSeed) \
                .filter_by(group=group) \
                .first()

    def begin_final_test(self, group: int):
        seed = str(uuid.uuid4())
        with self.db.create_session() as session:
            session.add(FinalSeed(group=group, seed=seed, active=True))

    def continue_final_test(self, group: int):
        with self.db.create_session() as session:
            session.query(FinalSeed) \
                .filter_by(group=group) \
                .update(dict(active=True))

    def end_final_test(self, group: int):
        with self.db.create_session() as session:
            session.query(FinalSeed) \
                .filter_by(group=group) \
                .update(dict(active=False))

    def delete_final_seed(self, group: int):
        with self.db.create_session() as session:
            session.query(FinalSeed) \
                .filter_by(group=group) \
                .delete()


class AppDatabase:
    def __init__(self, get_connection: Callable[[], str]):
        db = DbContextManager(get_connection)
        self.groups = GroupRepository(db)
        self.variants = VariantRepository(db)
        self.tasks = TaskRepository(db)
        self.statuses = TaskStatusRepository(db)
        self.messages = MessageRepository(db)
        self.checks = MessageCheckRepository(db)
        self.seeds = FinalSeedRepository(db)
