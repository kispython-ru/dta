import datetime
import time
import uuid
from typing import Callable

import pytest
from bs4 import BeautifulSoup

from flask.testing import FlaskClient

from webapp.managers import AppConfigManager, StudentManager
from webapp.models import TypeOfTask
from webapp.repositories import AppDatabase


def unique_str() -> str:
    unique_id = uuid.uuid4()
    return str(unique_id)


def unique_int() -> int:
    unique_id = uuid.uuid4().node
    return int(unique_id)


def timeout_assert(condition: Callable[[], bool], timeout: int = 20):
    delta = datetime.timedelta(seconds=timeout)
    started = datetime.datetime.now()
    while True:
        time.sleep(1)
        if datetime.datetime.now() > started + delta:
            raise Exception("Time is out, assertion failed.")
        if condition():
            break


def arrange_task(db: AppDatabase, type: TypeOfTask = TypeOfTask.Static) -> tuple[int, int, int]:
    variant = unique_int()
    group_name = unique_str()
    task = unique_int()

    db.variants.create_by_ids([variant])
    db.groups.create(group_name)
    db.tasks.create(task, type)

    group = db.groups.get_by_prefix(group_name)[0].id
    return (group, variant, task)


def get_tags(
    html: str,
    name: str,
    class_: str | bool,
):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(name, class_=class_)


def teacher_login(db: AppDatabase, client: FlaskClient):
    email = f'{unique_str()}@{unique_str()}.ru'
    password = unique_str()
    config = AppConfigManager(lambda: dict())
    students = StudentManager(config, db.students, db.mailers)
    students.create(email, password, True)
    db.students.confirm(email)
    return client.post("/login", data={
        "login": email,
        "password": password
    }, follow_redirects=True)


def mode(mode_name):
    return pytest.mark.parametrize('app', ([f'enable-{mode_name}']), indirect=True)
