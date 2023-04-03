from tests.utils import arrange_task, teacher_login

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_login_logout(db: AppDatabase, client: FlaskClient):
    response = teacher_login(db, client)

    assert "login" not in response.request.path
    assert "Выгрузка всех присланных сообщений" in response.get_data(as_text=True)

    response = client.get("/teacher/logout", follow_redirects=True)

    assert "login" in response.request.path


def test_false_login(db: AppDatabase, client: FlaskClient):
    response = client.post("/teacher/login", data={
        "login": "badLogin",
        "password": "evenWorsePassword"
    }, follow_redirects=True)

    assert "login" in response.request.path


def test_message_download(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)
    separator = ","
    count = 10
    response = client.get(f"teacher/messages?separator={separator}&count={count}")

    assert response.headers['Content-Disposition'] == 'attachment; filename=messages.csv'
    assert response.headers["Content-type"] == 'text/csv'

    file = list(filter(bool, response.get_data(as_text=True).splitlines()))
    assert file[0][1::] == 'ID,Время,Группа,Задача,Вариант,IP,Отправитель,Код'
    assert len(file) - 1 <= count


def test_group_select(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)

    group = 1
    response = client.get(f"teacher/group/select?group={group}", follow_redirects=True)
    assert db.groups.get_by_id(group).title in response.get_data(as_text=True)


def test_submission(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)

    gid, vid, tid = arrange_task(db)

    db.statuses.submit_task(tid, vid, gid, "test", "0.0.0.0")
    response = client.get(f"/teacher/submissions?gid={gid}&tid={tid}&vid={vid}", follow_redirects=True)

    assert response.status_code == 200
    assert str(gid) in response.get_data(as_text=True)
