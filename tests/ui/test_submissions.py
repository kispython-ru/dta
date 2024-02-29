from secrets import token_hex

from tests.database.test_check import arrange_task
from tests.utils import mode, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


@mode("registration")
def test_unauthorized_submissions(db: AppDatabase, client: FlaskClient):
    response = client.get('/submissions')
    html = response.get_data(as_text=True)

    assert "401 Unauthorized" in html


@mode("exam")
def test_empty_submissions(db: AppDatabase, client: FlaskClient):
    response = client.get('/submissions')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Список отправленных решений пуст" in html


@mode("exam")
def test_exam_anonymous_submissions(db: AppDatabase, client: FlaskClient):
    group_id, variant_id, task_id = arrange_task(db)

    session_id = token_hex(16)

    code = "main = lambda: 42" + unique_str()
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, None, session_id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test_exam_anonymous_submissions")

    client.set_cookie("localhost", "anonymous_identifier", session_id)
    response = client.get('/submissions')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert code in html


def test_no_reg_anonymous_submissions(db: AppDatabase, client: FlaskClient):
    group_id, variant_id, task_id = arrange_task(db)

    session_id = token_hex(16)

    code = "main = lambda: 42" + unique_str()
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, None, session_id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test_no_reg_anonymous_submissions")

    client.set_cookie("localhost", "anonymous_identifier", session_id)
    response = client.get('/submissions')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert code in html
