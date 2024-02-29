from tests.utils import get_tags, unique_int, unique_str

from secrets import token_hex

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase

from ..database.test_check import arrange_task
from ..utils import mode


@mode("exam")
def test_empty_submissions(db: AppDatabase, client: FlaskClient):
    response = client.get('/submissions')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Список отправленных решений пуст" in html


@mode("exam")
def test_anonymous_submissions(db: AppDatabase, client: FlaskClient):
    group_id, variant_id, task_id = arrange_task(db)

    session_id = token_hex(16)

    code = "main = lambda: 42"+unique_str()
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, None, session_id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    client.set_cookie("localhost", "anonymous_identifier", session_id)
    response = client.get('/submissions')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert code in html
