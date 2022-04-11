import json

from tests.utils import arrange_task

from flask.testing import FlaskClient

from webapp.models import Status
from webapp.repositories import AppDatabase


def test_task_status_list_fetching(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)

    response = client.get(f"/api/v1/group/{group}/variant/{variant}/task/list")

    assert response.is_json
    assert any(item for item in response.json if item["id"] == task)


def test_task_status_fetching(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)

    response = client.get(f"/api/v1/group/{group}/variant/{variant}/task/{task}")

    assert response.is_json
    assert response.json['id'] == task
    assert response.json['status'] == Status.NotSubmitted
    assert response.json['status_name'] == "Не отправлено"


def test_task_solution_submission(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)

    response = client.post(
        f"/api/v1/group/{group}/variant/{variant}/task/{task}",
        data=json.dumps(dict(code="main = lambda x: 42")),
        headers=dict(token="CHANGE_ME"),
        content_type='application/json'
    )

    assert response.json is not None
    assert response.json["id"] == task
    assert response.json["status"] == Status.Submitted
    assert response.json["status_name"] == "Отправлено"
    assert response.json["error_message"] is None


def test_unauthorized_submission(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)

    response = client.post(
        f"/api/v1/group/{group}/variant/{variant}/task/{task}",
        data=json.dumps(dict(code="main = lambda x: 42")),
        headers=dict(token="INVALID_TOKEN"),
        content_type='application/json'
    )

    assert response.json is not None
    assert response.json["error"] == 500
