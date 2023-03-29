from flask.testing import FlaskClient

from tests.utils import arrange_task
from webapp.managers import TeacherManager
from webapp.repositories import AppDatabase

TEST_LOGIN = "test"
TEST_PASSWORD = "testtest"


def test_exam_redirect(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_db, exam_client, TEST_LOGIN, TEST_PASSWORD)

    assert exam_client.application.config.get("FINAL_TASKS") is not None

    group = 1

    response = exam_client.get(f"teacher/group/select?group={group}", follow_redirects=True)
    assert "exam" in response.request.path
    assert exam_db.groups.get_by_id(group).title in response.get_data(as_text=True)
    assert "Зачёт" in response.get_data(as_text=True)


def test_exam_toggle(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_db, exam_client, TEST_LOGIN, TEST_PASSWORD)

    group = 1

    seed = exam_db.seeds.get_final_seed(group)
    if seed is None or not seed.active:
        response = exam_client.get(f"/teacher/group/{group}/exam/toggle", follow_redirects=True)
        assert response.status_code == 200
        assert "ИНБО-01-20" in response.get_data(as_text=True)
        assert "Завершить" in response.get_data(as_text=True)
        assert exam_db.seeds.get_final_seed(group).active

    response = exam_client.get(f"/teacher/group/{group}/exam/toggle", follow_redirects=True)
    assert response.status_code == 200
    assert "ИНБО-01-20" in response.get_data(as_text=True)
    assert "Продолжить зачёт" in response.get_data(as_text=True)
    assert not exam_db.seeds.get_final_seed(group).active


def test_exam_download(exam_db: AppDatabase, exam_client: FlaskClient):
    login(exam_db, exam_client, TEST_LOGIN, TEST_PASSWORD)

    exam_db.variants.create_by_ids([1])
    exam_db.groups.create("TEST")
    exam_db.tasks.create_by_ids([1])

    gid, vid, tid = 21, 1, 1
    student_email = "test@gmail.com"
    if not exam_db.students.find_by_email(student_email):
        exam_db.students.create(student_email, "123123123")
        exam_db.students.confirm(student_email)
        exam_db.students.update_group(exam_db
                                      .students
                                      .find_by_email(student_email), gid)

    exam_db.statuses.submit_task(tid, vid, gid, "main = lambda: 42", "0.0.0.0")

    response = exam_client.get(f"/teacher/group/{str(gid)}/exam/csv", follow_redirects=True)

    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == f'attachment; filename={gid}.csv'
    assert response.headers["Content-type"] == 'text/csv'


def login(db: AppDatabase, client: FlaskClient, login: str, password: str):
    if not db.teachers.find_by_login(login):
        tm = TeacherManager(db.teachers)
        tm.create(login, password)
    return client.post("/teacher/login", data={
        "login": login,
        "password": password
    }, follow_redirects=True)
