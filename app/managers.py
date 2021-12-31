from typing import List, Union
from flask_bcrypt import Bcrypt
from flask import current_app as app
from sqlalchemy.sql.sqltypes import DateTime
from app.models import Task, User, UserTask
from sqlalchemy.orm import Session
from enum import IntEnum
import datetime


class UserManager():
    def __init__(self, session: Session):
        self.session = session
        self.bcrypt = Bcrypt(app)

    def register(self, email: str, password: str) -> User:
        app.logger.info(f'Registering user {email}')
        password_hash = self.bcrypt.generate_password_hash(
            password).decode('utf8')
        user = User(email=email, password=password_hash)
        self.session.add(user)
        self.session.commit()
        return user

    def check_password(self, email: str, password: str) -> Union[User, None]:
        app.logger.info(f'Checking password for user {email}')
        user = self.session.query(User).filter_by(email=email).first()
        if user is None:
            return None
        check_result = self.bcrypt.check_password_hash(
            user.password, password)
        if check_result:
            return user
        return None

    def get_by_id(self, id: int) -> User:
        user = self.session.query(User).get(id)
        return user


class TaskStatus(IntEnum):
    Created = 0
    Submitted = 1
    Checking = 2
    Checked = 3


class UserTaskInfo():
    def __init__(self, task: Task, user_task: UserTask):
        self.task = task
        self.user_task = user_task
        self.status = TaskStatus(user_task.status)


class TaskManager():
    def __init__(self, session: Session):
        self.session = session

    def create_task(self, name: str) -> Task:
        app.logger.info(f'Creating task {name}')
        task = Task(name=name)
        self.session.add(task)
        self.session.commit()
        return task

    def create_user_task(self, user_id: int, task_id: int) -> UserTask:
        app.logger.info(f'Creating user task {task_id} for user {user_id}')
        status = TaskStatus.Created
        now = datetime.datetime.now()
        task = self.session.query(Task).get(task_id)
        user_task = UserTask(
            user_id=user_id,
            task_id=task.id,
            created_at=now,
            status=status)
        self.session.add(user_task)
        self.session.commit()
        return user_task

    def create_user_tasks(self, user_id: int) -> List[UserTask]:
        app.logger.info(f'Creating user tasks for user {user_id}')
        tasks = self.session.query(Task).all()
        user_tasks = []
        for task in tasks:
            user_task = self.create_user_task(user_id, task.id)
            user_tasks.append(user_task)
        return user_tasks

    def ensure_user_tasks_created(self, user_id: int) -> List[UserTaskInfo]:
        tasks = self.get_user_tasks(user_id)
        if len(tasks) is 0:
            self.create_user_tasks(user_id)
            return self.get_user_tasks(user_id)
        return list(tasks)

    def get_user_tasks(self, user_id: int) -> List[UserTaskInfo]:
        app.logger.info(f'Fetching user tasks for user {user_id}')
        user_tasks = self.session \
            .query(UserTask, Task) \
            .filter_by(user_id=user_id) \
            .join(Task, Task.id == UserTask.task_id)
        user_task_info = []
        for (user_task, task) in user_tasks.all():
            info = UserTaskInfo(user_task=user_task, task=task)
            user_task_info.append(info)
        return user_task_info
