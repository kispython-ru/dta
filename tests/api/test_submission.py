import json

from sqlalchemy.orm import Session
from tests.utils import unique_int, unique_str

from flask.testing import FlaskClient

from webapp.models import TaskStatusEnum
from webapp.repositories import AppDbContext


def test_solution_submission(session: Session, client: FlaskClient):
    variant = unique_int()
    task = unique_int()

    db = AppDbContext(session)
    group = db.groups.create(unique_str()).id
    db.variants.create_by_ids([variant])
    db.tasks.create_by_ids([task])

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


def test_unauthorized_submission(session: Session, client: FlaskClient):
    variant = unique_int()
    task = unique_int()

    db = AppDbContext(session)
    group = db.groups.create(unique_str()).id
    db.variants.create_by_ids([variant])
    db.tasks.create_by_ids([task])

    response = client.post(
        f"/api/v1/group/{group}/variant/{variant}/task/{task}",
        data=json.dumps(dict(code="main = lambda x: 42")),
        headers=dict(token="INVALID_TOKEN"),
        content_type='application/json'
    )

    assert response.json is not None
    assert response.json["error"] == 500
