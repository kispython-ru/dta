import datetime
import uuid
from typing import Callable, Dict, List, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from webapp.models import (
    FinalSeed,
    Group,
    Message,
    Task,
    TaskStatus,
    TaskStatusEnum,
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
        if exc_type is not None and exc_type is IntegrityError:
            self.session.rollback()
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

    def get_groupings(self) -> Dict[str, List[Group]]:
        groups = self.get_all()
        groupings: Dict[str, List[Group]] = {}
        for group in groups:
            key = group.title.split("-")[0]
            groupings.setdefault(key, []).append(group)
        return groupings

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
            session.commit()
            return group

    def delete_all(self):
        with self.db.create_session() as session:
            session.query(Group).delete()
            session.commit()


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
            session.commit()

    def delete_all(self):
        with self.db.create_session() as session:
            session.query(Task).delete()
            session.commit()


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
            session.commit()

    def delete_all(self):
        with self.db.create_session() as session:
            session.query(Variant).delete()
            session.commit()


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
            status: int,
            output: str):
        existing = self.get_task_status(task, variant, group)
        if existing is not None:
            if existing.status == TaskStatusEnum.Checked:
                return  # We've already accepted this task!
        with self.db.create_session() as session:
            session.query(TaskStatus) \
                .filter_by(task=task, variant=variant, group=group) \
                .update({"status": status, "output": output})
            session.commit()

    def submit_task(
            self,
            task: int,
            variant: int,
            group: int,
            code: str) -> TaskStatus:
        with self.db.create_session() as session:
            existing: TaskStatus = session.query(TaskStatus) \
                .filter_by(task=task, variant=variant, group=group) \
                .first()
            if existing is not None:
                if existing.status == TaskStatusEnum.Checked:
                    return  # We've already accepted this task!
                session.delete(existing)
                session.commit()
            now = datetime.datetime.now()
            status = TaskStatusEnum.Submitted
            task_status = TaskStatus(
                task=task,
                variant=variant,
                group=group,
                time=now,
                code=code,
                output=None,
                status=status,
            )
            session.add(task_status)
            session.commit()
            return task_status


class MessageRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def submit_task(
            self,
            task: int,
            variant: int,
            group: int,
            code: str,
            ip: str) -> Message:
        with self.db.create_session() as session:
            now = datetime.datetime.now()
            message = Message(
                task=task,
                variant=variant,
                group=group,
                time=now,
                code=code,
                ip=ip,
                processed=False,
            )
            session.add(message)
            session.commit()
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
                .order_by(Message.time.desc()) \
                .all()
            return pending

    def get_pending_messages_unique(self) -> List[Message]:
        pending_messages = self.get_pending_messages()
        unique_messages = []
        seen_keys = []
        for message in pending_messages:
            key = (message.group, message.variant, message.task)
            if key in seen_keys:
                continue
            seen_keys.append(key)
            unique_messages.append(message)
        return unique_messages

    def mark_as_processed(self, task: int, variant: int, group: int):
        with self.db.create_session() as session:
            session.query(Message) \
                .filter_by(task=task, variant=variant, group=group) \
                .update({"processed": True})
            session.commit()


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
            session.commit()

    def end_final_test(self, group: int):
        with self.db.create_session() as session:
            session.query(FinalSeed) \
                .filter_by(group=group) \
                .update({"active": False})
            session.commit()


class AppDatabase:
    def __init__(self, get_connection: Callable[[], str]):
        db = DbContextManager(get_connection)
        self.groups = GroupRepository(db)
        self.variants = VariantRepository(db)
        self.tasks = TaskRepository(db)
        self.statuses = TaskStatusRepository(db)
        self.messages = MessageRepository(db)
        self.seeds = FinalSeedRepository(db)
