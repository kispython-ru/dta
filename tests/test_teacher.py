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

    assert "Выгрузка всех присланных сообщений" in response.get_data(as_text=True)

    response = client.get("/teacher/logout", follow_redirects=True)

    assert "login" in response.request.path


def test_message_claim(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)

    response = client.get("teacher/messages", data={
        "separator": ",",
        "count": 10
    })

    assert response.headers['Content-Disposition'] == 'attachment; filename=messages.csv'
    assert response.headers["Content-type"] == 'text/csv'

    file = list(filter(bool, response.get_data(as_text=True).splitlines()))
    assert file[0][1::] == 'ID,Время,Группа,Задача,Вариант,IP,Отправитель,Код'
    assert len(file)-1 == len(db.messages.get_latest(None))


def login(client: FlaskClient, login: str, password: str):
    return client.post("/teacher/login", data={
        "login": login,
        "password": password
    }, follow_redirects=True)
