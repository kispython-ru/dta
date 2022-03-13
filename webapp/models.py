import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from flask import current_app as app


Base = declarative_base()


def create_session_manually(connection_string: str) -> Session:
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory()


def create_session() -> Session:
    connection_string = app.config["CONNECTION_STRING"]
    return create_session_manually(connection_string)


class Group(Base):
    __tablename__ = "groups"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    title = sa.Column("title", sa.String, unique=True, nullable=False)


class Task(Base):
    __tablename__ = "tasks"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)


class Variant(Base):
    __tablename__ = "variants"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)


class TaskStatus(Base):
    __tablename__ = "task_statuses"
    task = sa.Column(
        "task",
        sa.Integer,
        sa.ForeignKey("tasks.id"),
        primary_key=True,
        nullable=False,
    )
    variant = sa.Column(
        "variant",
        sa.Integer,
        sa.ForeignKey("variants.id"),
        primary_key=True,
        nullable=False,
    )
    group = sa.Column(
        "group",
        sa.Integer,
        sa.ForeignKey("groups.id"),
        primary_key=True,
        nullable=False,
    )
    time = sa.Column("time", sa.DateTime, nullable=False)
    code = sa.Column("code", sa.String, nullable=False)
    output = sa.Column("output", sa.String, nullable=True)
    status = sa.Column("status", sa.Integer, nullable=False)


class Message(Base):
    __tablename__ = "messages"
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    task = sa.Column(
        "task",
        sa.Integer,
        sa.ForeignKey("tasks.id"),
        nullable=False,
    )
    variant = sa.Column(
        "variant",
        sa.Integer,
        sa.ForeignKey("variants.id"),
        nullable=False,
    )
    group = sa.Column(
        "group",
        sa.Integer,
        sa.ForeignKey("groups.id"),
        nullable=False,
    )
    time = sa.Column("time", sa.DateTime, nullable=False)
    code = sa.Column("code", sa.String, nullable=False)
    ip = sa.Column("ip", sa.String, nullable=False)
    processed = sa.Column("processed", sa.Boolean, nullable=False)

    def __str__(self):
        return str({
            "id": self.id,
            "task": self.task,
            "variant": self.variant,
            "group": self.group,
            "time": self.time,
            "ip": self.ip,
            "processed": self.processed,
        })
