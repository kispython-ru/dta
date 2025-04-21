import enum
from functools import lru_cache
import json

import sqlalchemy as sa
from sqlalchemy import Engine
from sqlalchemy.orm import declarative_base, sessionmaker


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


Base = declarative_base()


def create_session_maker(engine: Engine) -> sessionmaker:
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory


class Group(Base):
    __tablename__ = "groups"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = sa.Column("title", sa.String, unique=True, nullable=False)
    external = sa.Column("external", sa.String, unique=False, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    formulation = sa.Column("formulation", sa.String, nullable=True)


class Variant(Base):
    __tablename__ = "variants"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)


class TaskStatus(Base):
    __tablename__ = "task_statuses"
    task = sa.Column("task", sa.Integer, sa.ForeignKey("tasks.id"), primary_key=True, nullable=False)
    variant = sa.Column("variant", sa.Integer, sa.ForeignKey("variants.id"), primary_key=True, nullable=False)
    group = sa.Column("group", sa.Integer, sa.ForeignKey("groups.id"), primary_key=True, nullable=False)
    time = sa.Column("time", sa.DateTime, nullable=False)
    code = sa.Column("code", sa.String, nullable=False)
    ip = sa.Column("ip", sa.String, nullable=False)
    output = sa.Column("output", sa.String, nullable=True)
    status = sa.Column("status", IntEnum(Status), nullable=False)
    achievements = sa.Column("achievements", JsonArray, nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    task = sa.Column("task", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False)
    variant = sa.Column("variant", sa.Integer, sa.ForeignKey("variants.id"), nullable=False)
    group = sa.Column("group", sa.Integer, sa.ForeignKey("groups.id"), nullable=False)
    time = sa.Column("time", sa.DateTime, nullable=False)
    code = sa.Column("code", sa.String, nullable=False)
    ip = sa.Column("ip", sa.String, nullable=False)
    session_id = sa.Column("session_id", sa.String, nullable=True)
    processed = sa.Column("processed", sa.Boolean, nullable=False)
    student = sa.Column("student", sa.Integer, sa.ForeignKey("students.id"), nullable=True)


class MessageCheck(Base):
    __tablename__ = "message_checks"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    message = sa.Column("message", sa.Integer, sa.ForeignKey("messages.id"), nullable=False)
    time = sa.Column('time', sa.DateTime, nullable=False)
    status = sa.Column('status', sa.Integer, nullable=False)
    output = sa.Column('output', sa.String, nullable=True)
    achievement = sa.Column('achievement', sa.Integer, nullable=True)


class FinalSeed(Base):
    __tablename__ = "final_seeds"
    seed = sa.Column("seed", sa.String, unique=True, nullable=False)
    active = sa.Column("active", sa.Boolean, nullable=False)
    group = sa.Column("group", sa.Integer, sa.ForeignKey('groups.id'), primary_key=True, nullable=False)


class Student(Base):
    __tablename__ = "students"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    external_id = sa.Column("external_id", sa.BigInteger, nullable=True)
    provider = sa.Column("provider", sa.String, nullable=True)
    email = sa.Column("email", sa.String, nullable=False)
    group = sa.Column("group", sa.String, nullable=True)
    variant = sa.Column("variant", sa.Integer, nullable=True)
    password_hash = sa.Column("password_hash", sa.String, nullable=True)
    unconfirmed_hash = sa.Column("unconfirmed_hash", sa.String, nullable=True)
    blocked = sa.Column("blocked", sa.Boolean, nullable=False)
    teacher = sa.Column("teacher", sa.Boolean, nullable=True)


class Mailer(Base):
    __tablename__ = "mailers"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    domain = sa.Column("domain", sa.String, nullable=False)


class AllowedIp(Base):
    __tablename__ = "allowed_ips"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    ip = sa.Column("ip", sa.String, nullable=False)
    label = sa.Column("label", sa.String, nullable=True)
