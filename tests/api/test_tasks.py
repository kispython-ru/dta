import json

from tests.utils import arrange_task

from flask.testing import FlaskClient

from webapp.models import TaskStatusEnum
from webapp.repositories import AppDatabase


def test_task_status_list_fetching(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)

    responce = client.get(f"/api/v1/group/{group}/variant/{variant}/task/list")

    assert responce.is_json
    assert any([item for item in responce.json if item["id"] == task])


def test_task_status_fetching(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)

    responce = client.get(f"/api/v1/group/{group}/variant/{variant}/task/{task}")

    assert responce.is_json
    assert responce.json['id'] == task
    assert responce.json['status'] == TaskStatusEnum.NotSubmitted
    assert responce.json['status_name'] == TaskStatusEnum.NotSubmitted.name


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
    assert response.json["status"] == TaskStatusEnum.Submitted
    assert response.json["status_name"] == TaskStatusEnum.Submitted.name
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
