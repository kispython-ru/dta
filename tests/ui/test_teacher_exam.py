from flask.testing import FlaskClient

from tests.utils import arrange_task, teacher_login
from webapp.managers import TeacherManager
from webapp.repositories import AppDatabase


def test_exam_redirect(exam_db: AppDatabase, exam_client: FlaskClient):
    teacher_login(exam_db, exam_client)

    assert exam_client.application.config.get("FINAL_TASKS") is not None

    group = 1

    response = exam_client.get(f"teacher/group/select?group={group}", follow_redirects=True)
    assert "exam" in response.request.path
    assert exam_db.groups.get_by_id(group).title in response.get_data(as_text=True)
    assert "Зачёт" in response.get_data(as_text=True)


def test_exam_toggle(exam_db: AppDatabase, exam_client: FlaskClient):
    teacher_login(exam_db, exam_client)

    group = 1
    seed = exam_db.seeds.get_final_seed(group)
    if (seed is None) or not seed.active:
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


def test_exam_download(exam_db: AppDatabase, exam_client: FlaskClient):
    teacher_login(exam_db, exam_client)


    gid, vid, tid = 1, 1, 1
    student_email = "test@gmail.com"
    if not exam_db.students.find_by_email(student_email):
        exam_db.students.create(student_email, "123123123")
        exam_db.students.confirm(student_email)
        exam_db.students.update_group(exam_db
                                      .students
                                      .find_by_email(student_email), gid)

    response = exam_client.get(f"/teacher/group/{gid}/exam/csv", follow_redirects=True)

    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == f'attachment; filename={gid}.csv'
    assert response.headers["Content-type"] == 'text/csv'
