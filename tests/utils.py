import datetime
import time
import uuid
from typing import Callable

import pytest
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from flask.testing import FlaskClient

from webapp.managers import StudentManager
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


def arrange_task(db: AppDatabase) -> tuple[int, int, int]:
    variant = unique_int()
    group_name = unique_str()
    task = unique_int()

    db.variants.create_by_ids([variant])
    db.groups.create(group_name)
    db.tasks.create_by_ids([task])

    group = db.groups.get_by_prefix(group_name)[0].id
    return (group, variant, task)


def get_tags(
    html: str,
    name: str,
    class_: str | bool | None,
) -> ResultSet[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(name, class_=class_)


def teacher_login(db: AppDatabase, client: FlaskClient):
    email = f'{unique_str()}@{unique_str()}.ru'
    password = unique_str()
    students = StudentManager(None, db.students, db.mailers)
    students.create(email, password, True)
    db.students.confirm(email)
    return client.post("/login", data={
        "login": email,
        "password": password
    }, follow_redirects=True)


def mode(mode_name):
    return pytest.mark.parametrize('app', ([f'enable-{mode_name}']), indirect=True)


def get_greeting_msg():
    current_time = datetime.now().time()
    get_time = lambda string_time: datetime.strptime(string_time, "%H:%M").time()
    if get_time("06:00") <= current_time < get_time("12:00"):
        return "Доброе утро"
    if get_time("12:00") <= current_time < get_time("18:00"):
        return "Добрый день"
    if get_time("18:00") <= current_time < get_time("22:00"):
        return "Добрый вечер"
    return "Доброй ночи"
