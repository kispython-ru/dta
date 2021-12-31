import sqlalchemy as sa
from app.utils import Base


class User(Base):
    __tablename__ = 'users'
    id = sa.Column("id", sa.Integer, primary_key=True, nullable=False)
    email = sa.Column("email", sa.String, unique=True, nullable=False)
    password = sa.Column("password", sa.String, nullable=False)


class Task(Base):
    __tablename__ = 'tasks'
    id = sa.Column('id', sa.Integer, primary_key=True, nullable=False)
    name = sa.Column('name', sa.String, unique=True, nullable=False)


class UserTask(Base):
    __tablename__ = 'user_tasks'
    user_id = sa.Column(
        'user_id',
        sa.Integer,
        sa.ForeignKey('users.id'),
        primary_key=True,
        nullable=False)
    task_id = sa.Column(
        'task_id',
        sa.Integer,
        sa.ForeignKey('tasks.id'),
        primary_key=True,
        nullable=False)
    created_at = sa.Column('created_at', sa.DateTime, nullable=False)
    status = sa.Column('status', sa.Integer, nullable=False)
