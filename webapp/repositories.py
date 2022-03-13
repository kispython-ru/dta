import datetime
from enum import IntEnum
from typing import Dict, List

from sqlalchemy.orm import Session

from webapp.models import Group, Message, Task, TaskStatus, Variant


class GroupRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Group]:
        groups = self.session.query(Group).all()
        return groups

    def get_groupings(self) -> Dict[str, List[Group]]:
        groups = self.get_all()
        groupings: Dict[str, List[Group]] = {}
        for group in groups:
            key = group.title.split("-")[0]
            groupings.setdefault(key, []).append(group)
        return groupings

    def get_by_id(self, group_id: int) -> Group:
        group = self.session.query(Group).get(group_id)
        return group

    def create_by_names(self, names: List[str]):
        for name in names:
            group = Group(title=name)
            self.session.add(group)
        self.session.commit()

    def delete_all(self):
        self.session.query(Group).delete()


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Task]:
        tasks = self.session.query(Task).all()
        return tasks

    def get_by_id(self, task_id: int) -> Task:
        task = self.session.query(Task).get(task_id)
        return task

    def create_by_ids(self, ids: List[int]):
        for task_id in ids:
            group = Task(id=task_id)
            self.session.add(group)
        self.session.commit()

    def delete_all(self):
        self.session.query(Task).delete()


class VariantRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Variant]:
        variants = self.session.query(Variant).all()
        return variants

    def get_by_id(self, variant_id: int) -> Variant:
        variant = self.session.query(Variant).get(variant_id)
        return variant

    def create_by_ids(self, ids: List[int]):
        for variant_id in ids:
            task = Variant(id=variant_id)
            self.session.add(task)
        self.session.commit()

    def delete_all(self):
        self.session.query(Variant).delete()


class TaskStatusEnum(IntEnum):
    Submitted = 0
    Checking = 1
    Checked = 2
    Failed = 3

    @property
    def name(self):
        return {
            self.Submitted: "Отправлено",
            self.Checking: "Проверяется",
            self.Checked: "Принято",
            self.Failed: "Ошибка!",
        }[self]

    @property
    def code(self):
        return {
            self.Submitted: "?",
            self.Checking: "...",
            self.Checked: "+",
            self.Failed: "x",
        }[self]

    @property
    def color(self):
        return {
            self.Submitted: "primary",
            self.Checking: "warning",
            self.Checked: "success",
            self.Failed: "danger",
        }[self]


class TaskStatusRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[TaskStatus]:
        statuses = self.session.query(TaskStatus).all()
        return statuses

    def get_task_status(
            self,
            task: int,
            variant: int,
            group: int) -> TaskStatus:
        status = self.session.query(TaskStatus) \
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
        self.session.query(TaskStatus) \
            .filter_by(task=task, variant=variant, group=group) \
            .update({"status": status, "output": output})
        self.session.commit()

    def submit_task(
            self,
            task: int,
            variant: int,
            group: int,
            code: str) -> TaskStatus:
        existing = self.get_task_status(task, variant, group)
        if existing is not None:
            if existing.status == TaskStatusEnum.Checked:
                return  # We've already accepted this task!
            self.session.delete(existing)
            self.session.commit()
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
        self.session.add(task_status)
        self.session.commit()
        return task_status


class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def submit_task(
            self,
            task: int,
            variant: int,
            group: int,
            code: str,
            ip: str) -> Message:
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
        self.session.add(message)
        self.session.commit()
        return message

    def get_all(self) -> List[Message]:
        messages = self.session.query(Message).order_by(Message.time.desc()).all()
        return messages

    def get_latest(self, count: int) -> List[Message]:
        latest_messages = (
            self.session.query(Message)
            .order_by(Message.time.desc())
            .limit(count)
            .all()
        )
        return latest_messages

    def get_pending_messages(self) -> List[Message]:
        pending = self.session.query(Message) \
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
        self.session.query(Message) \
            .filter_by(task=task, variant=variant, group=group) \
            .update({"processed": True})
        self.session.commit()


class AppDbContext:
    def __init__(self, session: Session):
        self.session = session

    @property
    def groups(self) -> GroupRepository:
        return GroupRepository(self.session)

    @property
    def tasks(self) -> TaskRepository:
        return TaskRepository(self.session)

    @property
    def variants(self) -> VariantRepository:
        return VariantRepository(self.session)

    @property
    def statuses(self) -> TaskStatusRepository:
        return TaskStatusRepository(self.session)

    @property
    def messages(self) -> MessageRepository:
        return MessageRepository(self.session)
