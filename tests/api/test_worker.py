import json

from tests.utils import arrange_task, mode, timeout_assert

from flask.testing import FlaskClient

from webapp.models import Status
from webapp.repositories import AppDatabase


@mode("worker")
def test_background_task_check(db: AppDatabase, client: FlaskClient):
    def post_code(url: str, code: str):
        return client.post(
            url,
            data=json.dumps(dict(code=code)),
            headers=dict(token="CHANGE_ME"),
            content_type='application/json'
        )

    group, variant, task = arrange_task(db)
    url = f"/api/v1/group/{group}/variant/{variant}/task/{task}"

    response = post_code(url, "main = lambda x: 42")
    assert response.json
    assert response.json["status"] == Status.Submitted
    timeout_assert(lambda: client.get(url).json["status"] == Status.Checked)

    post_code(url, "main = lambda x: 'forty-two'")
    timeout_assert(lambda: client.get(url).json["status"] == Status.CheckedFailed)

    post_code(url, "main = lambda x: 42")
    timeout_assert(lambda: client.get(url).json["status"] == Status.Checked)

    messages = db.messages.get(task=task, variant=variant, group=group)
    history = [Status.Checked, Status.CheckedFailed, Status.Checked]
    for index, status in enumerate(history):
        message = messages[index]
        check = db.checks.get(message=message.id)
        assert check.status == status
