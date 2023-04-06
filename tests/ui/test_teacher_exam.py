from tests.utils import arrange_task, mode, teacher_login, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


@mode("exam")
def test_exam_redirect(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)
    name = unique_str()
    group = db.groups.create(name)

    response = client.get(f"teacher/group/select?group={group.id}", follow_redirects=True)

    assert "exam" in response.request.path
    assert name in response.get_data(as_text=True)
    assert "Зачёт" in response.get_data(as_text=True)


@mode("exam")
def test_exam_toggle(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)

    group = 1
    seed = db.seeds.get_final_seed(group)
    if (seed is None) or not seed.active:
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


@mode("exam")
def test_exam_download(db: AppDatabase, client: FlaskClient):
    teacher_login(db, client)

    gid, vid, tid = arrange_task(db)
    student_email = unique_str()

    db.students.create(student_email, unique_str())
    db.students.confirm(student_email)
    db.students.update_group(db.students.find_by_email(student_email), gid)

    response = client.get(f"/teacher/group/{gid}/exam/csv", follow_redirects=True)

    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == f'attachment; filename={gid}.csv'
    assert response.headers["Content-type"] == 'text/csv'
