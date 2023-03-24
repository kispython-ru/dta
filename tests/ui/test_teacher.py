from flask.testing import FlaskClient

import pytest

from tests.utils import arrange_task
from webapp.models import Status, Teacher
from webapp.repositories import AppDatabase

import csv

from webapp.managers import TeacherManager

TEST_LOGIN = "test"
TEST_PASSWORD = "testtest"


def test_login_logout(exam_db: AppDatabase, exam_client: FlaskClient):
    if not exam_db.teachers.find_by_login(TEST_LOGIN):
        exam_db.teachers.create(TEST_LOGIN, TEST_PASSWORD)

    exam_db.students.confirm("test@test.ru")

    response = login(exam_client, TEST_LOGIN, TEST_PASSWORD)

    assert "login" not in response.request.path
    assert "Выгрузка всех присланных сообщений" in response.get_data(as_text=True)

    response = exam_client.get("/teacher/logout", follow_redirects=True)

    assert "login" in response.request.path


def test_false_login(exam_db: AppDatabase, exam_client: FlaskClient):
    response = login(exam_client, "bad_login", "even_worse_password")
    assert "login" in response.request.path


def test_message_download(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_client, TEST_LOGIN, TEST_PASSWORD)
    separator = ","
    count = 10
    response = exam_client.get(f"teacher/messages?separator={separator}&count={count}")

    assert response.headers['Content-Disposition'] == 'attachment; filename=messages.csv'
    assert response.headers["Content-type"] == 'text/csv'

    file = list(filter(bool, response.get_data(as_text=True).splitlines()))
    assert file[0][1::] == 'ID,Время,Группа,Задача,Вариант,IP,Отправитель,Код'
    assert len(file) - 1 == count


def test_group_select(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_client, TEST_LOGIN, TEST_PASSWORD)

    for group in range(1, 10):
        response = exam_client.get(f"teacher/group/select?group={group}", follow_redirects=True)
        assert exam_db.groups.get_by_id(group).title in response.get_data(as_text=True)


def test_exam_redirect(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_client, TEST_LOGIN, TEST_PASSWORD)

    assert exam_client.application.config.get("FINAL_TASKS") is not None

    for group in range(1, 10):
        response = exam_client.get(f"teacher/group/select?group={group}", follow_redirects=True)
        assert "exam" in response.request.path
        assert exam_db.groups.get_by_id(group).title in response.get_data(as_text=True)
        assert "Зачёт" in response.get_data(as_text=True)


def test_exam_toggle(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_client, TEST_LOGIN, TEST_PASSWORD)

    for group in range(1, 10):

        seed = exam_db.seeds.get_final_seed(group)
        if seed is None or not seed.active:
            response = exam_client.get(f"/teacher/group/{group}/exam/toggle", follow_redirects=True)
            assert response.status_code == 200
            assert exam_db.groups.get_by_id(group).title in response.get_data(as_text=True)
            assert "Завершить" in response.get_data(as_text=True)
            assert exam_db.seeds.get_final_seed(group).active

        response = exam_client.get(f"/teacher/group/{group}/exam/toggle", follow_redirects=True)
        assert response.status_code == 200
        assert exam_db.groups.get_by_id(group).title in response.get_data(as_text=True)
        assert "Продолжить зачёт" in response.get_data(as_text=True)
        assert not exam_db.seeds.get_final_seed(group).active


"""# TODO

def test_submission(db: AppDatabase, client: FlaskClient):
    login(client, TEST_LOGIN, TEST_PASSWORD)

    gid, vid, tid = arrange_task(db)

    db.statuses.submit_task(tid, vid, gid, "test", "0.0.0.0")
    response = client.get(f"/teacher/submissions?god={gid}&tid={tid}&vid={vid}", follow_redirects=True)

    assert response.status_code == 200
    assert str(gid) in response.get_data(as_text=True)


# TODO


def test_exam_download(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_client, TEST_LOGIN, TEST_PASSWORD)
    count = 10
    gid = 8
    response = exam_client.get(f"/teacher/group/{gid}/exam/csv?delimiter=semicolon")

    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == f'attachment; filename={gid}.csv'
    assert response.headers["Content-type"] == 'text/csv'

    file = list(filter(bool, response.get_data(as_text=True).splitlines()))
    assert file[0][1::] == 'ID,Время,Группа,Задача,Вариант,IP,Отправитель,Код'
    assert len(file) - 1 == count"""


def login(client: FlaskClient, login: str, password: str):
    return client.post("/teacher/login", data={
        "login": login,
        "password": password
    }, follow_redirects=True)
