from tests.utils import arrange_task, mode, teacher_login, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase
from webapp.views.student import hide_email_filter


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

    group = db.groups.create(unique_str())

    response = client.get(f"teacher/group/select?group={group.id}", follow_redirects=True)
    assert group.title in response.get_data(as_text=True)


@mode('registration')
def test_submission(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)

    gid, vid, tid = arrange_task(db)

    student_email = f"{unique_str()}@lol.ru"

    student = db.students.create(student_email, unique_str())
    db.students.confirm(student_email)
    db.students.update_group(db.students.find_by_email(student_email), gid)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    mes = db.messages.submit_task(tid, vid, gid, code, ip, student.id)
    stat = db.statuses.submit_task(tid, vid, gid, code, ip)
    db.checks.record_check(mes.id, stat.status, "lol")

    response = client.get(f"/teacher/submissions/group/{gid}/variant/{vid}/task/{tid}")

    assert db.groups.get_by_id(gid).title in response.get_data(as_text=True)
    assert code in response.get_data(as_text=True)
    assert hide_email_filter(student_email) in response.get_data(as_text=True)
    assert str(student.id) in response.get_data(as_text=True)


def test_anonymous_submission(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)
    gid, vid, tid = arrange_task(db)
    code = "main = lambda: 42"
    ip = "0.0.0.0"

    mes = db.messages.submit_task(tid, vid, gid, code, ip, None)
    stat = db.statuses.submit_task(tid, vid, gid, code, ip)

    check = unique_str()

    db.checks.record_check(mes.id, stat.status, check)

    response = client.get(f"/teacher/submissions/group/{gid}/variant/{vid}/task/{tid}")

    assert db.groups.get_by_id(gid).title in response.get_data(as_text=True)
    assert code in response.get_data(as_text=True)
    assert "студент" not in response.get_data(as_text=True)
