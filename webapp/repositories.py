import datetime
import uuid
from typing import Callable

from sqlalchemy import desc, null
from sqlalchemy.orm import Session

from webapp.models import (
    FinalSeed,
    Group,
    Mailer,
    Message,
    MessageCheck,
    Status,
    Student,
    Task,
    TaskStatus,
    Teacher,
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

    def get_all(self) -> list[Group]:
        with self.db.create_session() as session:
            groups = session.query(Group).all()
            return groups

    def get_by_prefix(self, prefix: str) -> list[Group]:
        with self.db.create_session() as session:
            groups = session.query(Group) \
                .filter(Group.title.startswith(prefix)) \
                .all()
            return groups

    def get_by_id(self, group_id: int) -> Group:
        with self.db.create_session() as session:
            group = session.query(Group).get(group_id)
            return group

    def create_by_names(self, names: list[str]):
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

    def get_all(self) -> list[Task]:
        with self.db.create_session() as session:
            tasks = session.query(Task).all()
            return tasks

    def get_by_id(self, task_id: int) -> Task:
        with self.db.create_session() as session:
            task = session.query(Task).get(task_id)
            return task

    def create_by_ids(self, ids: list[int]):
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

    def get_all(self) -> list[Variant]:
        with self.db.create_session() as session:
            variants = session.query(Variant).all()
            return variants

    def get_by_id(self, variant_id: int) -> Variant:
        with self.db.create_session() as session:
            variant = session.query(Variant).get(variant_id)
            return variant

    def create_by_ids(self, ids: list[int]):
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

    def get_all(self) -> list[TaskStatus]:
        with self.db.create_session() as session:
            statuses = session.query(TaskStatus).all()
            return statuses

    def get_by_group(self, group: int) -> list[TaskStatus]:
        with self.db.create_session() as session:
            statuses = session.query(TaskStatus) \
                .filter_by(group=group) \
                .all()
            return statuses

    def get_with_groups(self) -> list[tuple[Group, TaskStatus]]:
        with self.db.create_session() as session:
            statuses = session.query(Group, TaskStatus) \
                .join(TaskStatus, TaskStatus.group == Group.id) \
                .filter((TaskStatus.status == Status.Checked) |
                        (TaskStatus.status == Status.CheckedFailed) |
                        (TaskStatus.status == Status.CheckedSubmitted)) \
                .all()
            return statuses

    def get_task_status(self, task: int, variant: int, group: int) -> TaskStatus | None:
        with self.db.create_session() as session:
            status = session.query(TaskStatus) \
                .filter_by(task=task, variant=variant, group=group) \
                .first()
            return status

    def delete_group_task_statuses(self, group: int):
        with self.db.create_session() as session:
            status = session.query(TaskStatus) \
                .filter_by(group=group) \
                .delete()
            return status

    def record_achievement(self, task: int, variant: int, group: int, achievement: int):
        existing = self.get_task_status(task, variant, group)
        if not existing:
            return
        achievements = list(set(existing.achievements + [achievement]))
        with self.db.create_session() as session:
            session.query(TaskStatus) \
                .filter_by(task=task, variant=variant, group=group) \
                .update(dict(achievements=achievements))

    def clear_achievements(self):
        with self.db.create_session() as session:
            session.query(TaskStatus) \
                .update(dict(achievements=None))

    def check(self, task: int, variant: int, group: int, code: str, ok: bool, output: str, ip: str):
        def status():
            existing = self.get_task_status(task, variant, group)
            if existing and existing.status in [Status.Checked, Status.CheckedFailed, Status.CheckedSubmitted]:
                return Status.Checked if ok else Status.CheckedFailed
            return Status.Checked if ok else Status.Failed

        return self.create_or_update(task, variant, group, code, status(), output, ip)

    def submit_task(self, task: int, variant: int, group: int, code: str, ip: str) -> TaskStatus:
        checked = [Status.Checked, Status.CheckedFailed, Status.CheckedSubmitted]
        existing = self.get_task_status(task, variant, group)
        status = Status.CheckedSubmitted if existing and existing.status in checked else Status.Submitted
        return self.create_or_update(task, variant, group, code, status, None, ip)

    def create_or_update(self, task: int, variant: int, group: int, code: str, status: int, output: str, ip: str):
        now = datetime.datetime.now()
        with self.db.create_session() as session:
            query = session.query(TaskStatus).filter_by(task=task, variant=variant, group=group)
            if query.count():
                query.update(dict(code=code, status=status, output=output, ip=ip, time=now))
                updated: TaskStatus = query.one()
                return updated
            model = TaskStatus(
                time=now,
                task=task,
                variant=variant,
                group=group,
                code=code,
                status=status,
                output=output,
                ip=ip)
            session.add(model)
            return model


class MessageRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def submit_task(
        self,
        task: int,
        variant: int,
        group: int,
        code: str,
        ip: str,
        student: int | None,
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
                student=student,
            )
            session.add(message)
            return message

    def get_all(self) -> list[Message]:
        with self.db.create_session() as session:
            messages = session.query(Message) \
                .order_by(Message.time.desc()) \
                .all()
            return messages

    def get_latest(self, count: int) -> list[Message]:
        with self.db.create_session() as session:
            latest_messages = session.query(Message) \
                .order_by(Message.time.desc()) \
                .limit(count) \
                .all()
            return latest_messages

    def get_pending_messages(self) -> list[Message]:
        with self.db.create_session() as session:
            pending = session.query(Message) \
                .filter_by(processed=False) \
                .order_by(Message.time.asc()) \
                .all()
            return pending

    def get_next_pending_message(self) -> Message | None:
        with self.db.create_session() as session:
            message = session.query(Message) \
                .filter_by(processed=False) \
                .order_by(Message.time.asc()) \
                .first()
            return message

    def get_by_id(self, id: int) -> Message:
        with self.db.create_session() as session:
            message = session.query(Message) \
                .filter_by(id=id) \
                .one()
            return message

    def get(self, task: int, variant: int, group: int) -> list[Message]:
        with self.db.create_session() as session:
            return session.query(Message) \
                .filter_by(task=task, variant=variant, group=group) \
                .order_by(Message.time.desc()) \
                .all()

    def mark_as_processed(self, message: int):
        with self.db.create_session() as session:
            session.query(Message) \
                .filter_by(id=message) \
                .update(dict(processed=True))


class MessageCheckRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get(self, message: int) -> MessageCheck:
        with self.db.create_session() as session:
            return session.query(MessageCheck) \
                .filter_by(message=message) \
                .first()

    def checked(self) -> list[MessageCheck]:
        with self.db.create_session() as session:
            return session.query(MessageCheck) \
                .filter_by(status=Status.Checked) \
                .all()

    def get_by_student(self, student: Student, skip: int, take: int) -> list[tuple[MessageCheck, Message]]:
        with self.db.create_session() as session:
            return session.query(MessageCheck, Message) \
                .join(Message, Message.id == MessageCheck.message) \
                .filter(Message.student == student.id) \
                .order_by(desc(Message.time)) \
                .offset(skip) \
                .limit(take) \
                .all()

    def get_by_task(self, group: int, variant: int, task: int, skip: int, take: int, registration: bool):
        with self.db.create_session() as session:
            query = session \
                .query(MessageCheck, Message, Student if registration else null()) \
                .join(Message, Message.id == MessageCheck.message)
            if registration:
                query = query.join(Student, Student.id == Message.student)
            return query \
                .filter(Message.group == group, Message.variant == variant, Message.task == task) \
                .order_by(desc(Message.time)) \
                .offset(skip) \
                .limit(take) \
                .all()

    def record_check(
        self,
        message: int,
        status: TaskStatus,
        output: str | None,
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

    def get_final_seed(self, group: int) -> FinalSeed | None:
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


class TeacherRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_by_id(self, id: int) -> Teacher | None:
        with self.db.create_session() as session:
            teacher = session.query(Teacher).get(id)
            return teacher

    def find_by_login(self, login: str) -> Teacher | None:
        with self.db.create_session() as session:
            teacher = session.query(Teacher) \
                .filter_by(login=login) \
                .first()
            return teacher


class StudentRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def get_by_id(self, id: int) -> Student | None:
        with self.db.create_session() as session:
            student = session.query(Student).get(id)
            return student

    def get_by_external(self, external_id: str, provider: str) -> Student | None:
        with self.db.create_session() as session:
            return (
                session.query(Student)
                .filter_by(external_id=external_id, provider=provider)
                .first()
            )

    def find_by_email(self, email: str) -> Student | None:
        email = email.lower()
        with self.db.create_session() as session:
            student = session.query(Student) \
                .filter_by(email=email) \
                .first()
            return student

    def change_password(self, email: str, password: str) -> bool:
        email = email.lower()
        with self.db.create_session() as session:
            query = session.query(Student).filter_by(email=email)
            student: Student = query.first()
            if student.unconfirmed_hash is not None:
                return False
            query.update(dict(unconfirmed_hash=password))

    def confirm(self, email: str):
        email = email.lower()
        with self.db.create_session() as session:
            query = session.query(Student).filter_by(email=email)
            student: Student = query.first()
            if student.unconfirmed_hash is not None:
                query.update(dict(
                    password_hash=student.unconfirmed_hash,
                    unconfirmed_hash=None,
                ))

    def create(self, email: str, password: str) -> Student:
        email = email.lower()
        with self.db.create_session() as session:
            student = Student(email=email, unconfirmed_hash=password, blocked=False)
            session.add(student)
            return student

    def create_external(
        self,
        email: str,
        external_id: int,
        group: str | None,
        provider: str,
    ) -> Student:
        with self.db.create_session() as session:
            student = Student(
                email=email,
                external_id=external_id,
                group=group,
                provider=provider,
                blocked=False,
            )
            session.add(student)
            return student

    def update_group(self, student: Student, group: str | None):
        with self.db.create_session() as session:
            session.query(Student).filter_by(id=student.id).update(dict(group=group))


class MailerRepository:
    def __init__(self, db: DbContextManager):
        self.db = db

    def exists(self, domain: str) -> bool:
        with self.db.create_session() as session:
            mailer = session.query(Mailer) \
                .filter_by(domain=domain) \
                .first()
            return bool(mailer)

    def get_domains(self) -> list[str]:
        with self.db.create_session() as session:
            mailers: list[Mailer] = session.query(Mailer).all()
            return [mailer.domain for mailer in mailers]


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
        self.teachers = TeacherRepository(db)
        self.students = StudentRepository(db)
        self.mailers = MailerRepository(db)
