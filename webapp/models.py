import enum
import json
from datetime import datetime
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class IntEnum(sa.TypeDecorator):
    impl = sa.Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value
        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)


class JsonArray(sa.TypeDecorator):
    impl = sa.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if not value:
            return '[]'
        if isinstance(value, list):
            return json.dumps(value)
        raise ValueError("Bad value type for JSON array.")

    def process_result_value(self, value, dialect):
        if not value:
            return []
        return json.loads(value)


class Status(enum.IntEnum):
    Submitted = 0
    Checked = 2
    Failed = 3
    NotSubmitted = 4
    CheckedSubmitted = 5
    CheckedFailed = 6


class TypeOfTask(enum.IntEnum):
    Static = 0
    Random = 1


class Base(DeclarativeBase):
    __abstract__ = True

    type_annotation_map = {
        list: JsonArray(),
        Status: IntEnum(Status),
        TypeOfTask: IntEnum(TypeOfTask),
        datetime: sa.DateTime(),
    }


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(unique=True)
    external: Mapped[str | None]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    formulation: Mapped[str | None]
    type: Mapped[TypeOfTask]


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TaskStatus(Base):
    __tablename__ = "task_statuses"

    task: Mapped[int] = mapped_column(sa.ForeignKey("tasks.id"), primary_key=True)
    variant: Mapped[int] = mapped_column(sa.ForeignKey("variants.id"), primary_key=True)
    group: Mapped[int] = mapped_column(sa.ForeignKey("groups.id"), primary_key=True)
    time: Mapped[datetime]
    code: Mapped[str]
    ip: Mapped[str]
    output: Mapped[str | None]
    status: Mapped[Status]
    achievements: Mapped[list | None]


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task: Mapped[int] = mapped_column(sa.ForeignKey("tasks.id"))
    variant: Mapped[int] = mapped_column(sa.ForeignKey("variants.id"))
    group: Mapped[int] = mapped_column(sa.ForeignKey("groups.id"))
    time: Mapped[datetime]
    code: Mapped[str]
    ip: Mapped[str]
    session_id: Mapped[str | None]
    processed: Mapped[bool]
    student: Mapped[int | None] = mapped_column(sa.ForeignKey("students.id"))


class MessageCheck(Base):
    __tablename__ = "message_checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message: Mapped[int] = mapped_column(sa.ForeignKey("messages.id"))
    time: Mapped[datetime]
    status: Mapped[Status]
    output: Mapped[str | None]
    achievement: Mapped[int | None]


class FinalSeed(Base):
    __tablename__ = "final_seeds"

    seed: Mapped[str] = mapped_column(unique=True)
    active: Mapped[bool]
    group: Mapped[int] = mapped_column(sa.ForeignKey("groups.id"), primary_key=True)


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[int | None] = mapped_column(sa.BigInteger)
    provider: Mapped[str | None]
    email: Mapped[str]
    group: Mapped[int | None]
    variant: Mapped[int | None]
    password_hash: Mapped[str | None]
    unconfirmed_hash: Mapped[str | None]
    blocked: Mapped[bool]
    teacher: Mapped[bool | None]


class Mailer(Base):
    __tablename__ = "mailers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str]


class AllowedIp(Base):
    __tablename__ = "allowed_ips"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip: Mapped[str]
    label: Mapped[str | None]


@lru_cache
def get_or_create_session_maker(connection: str) -> sessionmaker:
    engine = create_engine(connection)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
