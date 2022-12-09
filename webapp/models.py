import enum
import sqlalchemy as sa
import json

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


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
    Checking = 1
    Checked = 2
    Failed = 3
    NotSubmitted = 4


Base = declarative_base()


def create_session_maker(connection_string: str) -> sessionmaker:
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory


class Group(Base):
    __tablename__ = "groups"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    title = sa.Column("title", sa.String, unique=True, nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    formulation = sa.Column("formulation", sa.String, nullable=True)


class Variant(Base):
    __tablename__ = "variants"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)


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
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    task = sa.Column("task", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False)
    variant = sa.Column("variant", sa.Integer, sa.ForeignKey("variants.id"), nullable=False)
    group = sa.Column("group", sa.Integer, sa.ForeignKey("groups.id"), nullable=False)
    time = sa.Column("time", sa.DateTime, nullable=False)
    code = sa.Column("code", sa.String, nullable=False)
    ip = sa.Column("ip", sa.String, nullable=False)
    processed = sa.Column("processed", sa.Boolean, nullable=False)
    student = sa.Column("student", sa.Integer, sa.ForeignKey("students.id"), nullable=True)


class MessageCheck(Base):
    __tablename__ = "message_checks"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    message = sa.Column("message", sa.Integer, sa.ForeignKey("messages.id"), nullable=False)
    time = sa.Column('time', sa.DateTime, nullable=False)
    status = sa.Column('status', sa.Integer, nullable=False)
    output = sa.Column('output', sa.String, nullable=True)


class FinalSeed(Base):
    __tablename__ = "final_seeds"
    seed = sa.Column("seed", sa.String, unique=True, nullable=False)
    active = sa.Column("active", sa.Boolean, nullable=False)
    group = sa.Column("group", sa.Integer, sa.ForeignKey('groups.id'), primary_key=True, nullable=False)


class Teacher(Base):
    __tablename__ = "teachers"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    login = sa.Column("login", sa.String, nullable=False)
    password_hash = sa.Column("password_hash", sa.String, nullable=False)


class Student(Base):
    __tablename__ = "students"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    email = sa.Column("email", sa.String, nullable=False)
    password_hash = sa.Column("password_hash", sa.String, nullable=True)
    unconfirmed_hash = sa.Column("unconfirmed_hash", sa.String, nullable=True)
    blocked = sa.Column("blocked", sa.Boolean, nullable=False)


class Mailer(Base):
    __tablename__ = "mailers"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    domain = sa.Column("domain", sa.String, nullable=False)
