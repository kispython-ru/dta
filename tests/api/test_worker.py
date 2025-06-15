import json

from tests.utils import arrange_task, mode, timeout_assert

from flask.testing import FlaskClient

from webapp.models import Status
from webapp.repositories import AppDatabase


def post_code(client: FlaskClient, url: str, code: str):
    data = json.dumps(dict(code=code))
    headers = dict(token="CHANGE_ME")
    return client.post(url, data=data, headers=headers, content_type='application/json')


def check_status(client: FlaskClient, url: str, expected: Status):
    json = client.get(url).json
    return json and json['status'] == expected


@mode("worker")
def test_background_task_check(db: AppDatabase, client: FlaskClient):
    group, variant, task = arrange_task(db)
    url = f"/api/v1/group/{group}/variant/{variant}/task/{task}"

    response = post_code(client, url, "main = lambda x: 42")
    assert response.json
    assert response.json["status"] == Status.Submitted
    timeout_assert(lambda: check_status(client, url, Status.Checked))

    post_code(client, url, "main = lambda x: 'forty-two'")
    timeout_assert(lambda: check_status(client, url, Status.CheckedFailed))

    post_code(client, url, "main = lambda x: 42")
    timeout_assert(lambda: check_status(client, url, Status.Checked))

    messages = db.messages.get(task=task, variant=variant, group=group)
    for i, status in enumerate([
        Status.Checked,
        Status.CheckedFailed,
        Status.Checked,
    ]):
        check = db.checks.get(messages[i].id)
        assert check
        assert check.status == status
