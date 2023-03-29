from flask.testing import FlaskClient

import pytest

from tests.utils import arrange_task
from webapp.models import Status, Teacher
from webapp.repositories import AppDatabase

import csv

from webapp.managers import TeacherManager

TEST_LOGIN = "test"
TEST_PASSWORD = "testtest"


def test_login_logout(db: AppDatabase, client: FlaskClient):
    response = login(db, client, TEST_LOGIN, TEST_PASSWORD)

    assert "login" not in response.request.path
    assert "Выгрузка всех присланных сообщений" in response.get_data(as_text=True)

    response = client.get("/teacher/logout", follow_redirects=True)

    assert "login" in response.request.path


def test_false_login(db: AppDatabase, client: FlaskClient):
    response = login(db, client, "bad_login", "even_worse_password")
    assert "login" in response.request.path


def test_message_download(db: AppDatabase, client: FlaskClient):
    login(db, client, TEST_LOGIN, TEST_PASSWORD)
    separator = ","
    count = 10
    response = client.get(f"teacher/messages?separator={separator}&count={count}")

    assert response.headers['Content-Disposition'] == 'attachment; filename=messages.csv'
    assert response.headers["Content-type"] == 'text/csv'

    file = list(filter(bool, response.get_data(as_text=True).splitlines()))
    assert file[0][1::] == 'ID,Время,Группа,Задача,Вариант,IP,Отправитель,Код'
    assert len(file) - 1 <= count


def test_group_select(db: AppDatabase, client: FlaskClient):
    login(db, client, TEST_LOGIN, TEST_PASSWORD)

    group = 1
    response = client.get(f"teacher/group/select?group={group}", follow_redirects=True)
    assert db.groups.get_by_id(group).title in response.get_data(as_text=True)


"""# TODO

def test_submission(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)

    gid, vid, tid = arrange_task(db)

    db.statuses.submit_task(tid, vid, gid, "test", "0.0.0.0")
    response = client.get(f"/teacher/submissions?god={gid}&tid={tid}&vid={vid}", follow_redirects=True)

    assert response.status_code == 200
    assert str(gid) in response.get_data(as_text=True)

"""


def login(db: AppDatabase, client: FlaskClient, login: str, password: str):
    if not db.teachers.find_by_login(TEST_LOGIN) and login != "bad_login":
        tm = TeacherManager(db.teachers)
        tm.create(TEST_LOGIN, TEST_PASSWORD)
    return client.post("/teacher/login", data={
        "login": login,
        "password": password
    }, follow_redirects=True)
