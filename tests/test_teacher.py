from flask.testing import FlaskClient

import pytest

from webapp.models import Status, Teacher
from webapp.repositories import AppDatabase

import csv

from webapp.managers import TeacherManager

TEST_LOGIN = "test"
TEST_PASSWORD = "testtest"


def test_login_logout(db: AppDatabase, client: FlaskClient):
    if not db.teachers.find_by_login(TEST_LOGIN):
        db.teachers.create(TEST_LOGIN, TEST_PASSWORD)

    response = login(client, TEST_LOGIN, TEST_PASSWORD)

    assert "login" not in response.request.path
    assert "Выгрузка всех присланных сообщений" in response.get_data(as_text=True)

    response = client.get("/teacher/logout", follow_redirects=True)

    assert "login" in response.request.path


def test_false_login(db: AppDatabase, client: FlaskClient):
    response = login(client, "bad_login", "even_worse_password")
    assert "login" in response.request.path


def test_message_download(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)
    separator = ","
    count = 10
    response = client.get(f"teacher/messages?separator={separator}&count={count}")

    assert response.headers['Content-Disposition'] == 'attachment; filename=messages.csv'
    assert response.headers["Content-type"] == 'text/csv'

    file = list(filter(bool, response.get_data(as_text=True).splitlines()))
    assert file[0][1::] == 'ID,Время,Группа,Задача,Вариант,IP,Отправитель,Код'
    assert len(file) - 1 == count


def test_group_select(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)

    for group in range(1, 10):
        response = client.get(f"teacher/group/select?group={group}", follow_redirects=True)
        assert db.groups.get_by_id(group).title in response.get_data(as_text=True)


# With final tasks
def test_exam_redirect(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)

    assert client.application.config.get("FINAL_TASKS") is not None

    for group in range(1, 10):
        response = client.get(f"teacher/group/select?group={group}", follow_redirects=True)
        assert db.groups.get_by_id(group).title in response.get_data(as_text=True)
        assert "Зачёт" in response.get_data(as_text=True)


# With final tasks
def test_exam_toggle(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)

    for group in range(1, 10):

        seed = db.seeds.get_final_seed(group)
        if seed is None or not seed.active:
            response = client.get(f"/teacher/group/{group}/exam/toggle", follow_redirects=True)
            assert response.status_code == 200
            assert db.groups.get_by_id(group).title in response.get_data(as_text=True)
            assert "Завершить" in response.get_data(as_text=True)
            assert db.seeds.get_final_seed(group).active

        response = client.get(f"/teacher/group/{group}/exam/toggle", follow_redirects=True)
        assert response.status_code == 200
        assert db.groups.get_by_id(group).title in response.get_data(as_text=True)
        assert "Продолжить зачёт" in response.get_data(as_text=True)
        assert not db.seeds.get_final_seed(group).active


def login(client: FlaskClient, login: str, password: str):
    return client.post("/teacher/login", data={
        "login": login,
        "password": password
    }, follow_redirects=True)
