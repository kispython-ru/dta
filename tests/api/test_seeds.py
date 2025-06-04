import json

from tests.utils import arrange_task, mode, unique_int

from flask.testing import FlaskClient

from webapp.models import Status, TypeOfTask
from webapp.repositories import AppDatabase


def test_final_seed_is_not_used(db: AppDatabase, client: FlaskClient):
    (group, var, task) = arrange_task(db)
    group = db.groups.get_by_id(group)

    default_template = f'/files/task/{task}/group/{group.id}/variant/{var}#вариант-{var + 1}'
    response = client.get(f"/api/v1/group/{group.id}/variant/{var}/task/{task}")

    assert response.is_json
    assert response.json['id'] == task
    assert default_template in response.json['source']
    assert response.json['status'] == Status.NotSubmitted
    assert response.json['status_name'] == "Не отправлено"


@mode("exam")
def test_final_seed_is_used(db: AppDatabase, client: FlaskClient):
    task = 0
    group, var, _ = arrange_task(db, TypeOfTask.Random)
    title = db.groups.get_by_id(group).title

    db.tasks.create(task, TypeOfTask.Random)
    db.seeds.begin_final_test(group)

    default_template = f'/{task}/{title}.html#вариант-{var + 1}'
    response = client.get(f"/api/v1/group/{group}/variant/{var}/task/{task}")

    assert response.is_json
    assert response.json['id'] == task
    assert default_template not in response.json['source']
    assert response.json['status'] == Status.NotSubmitted
    assert response.json['status_name'] == "Не отправлено"


def test_final_submissions_are_allowed(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)
    db.seeds.begin_final_test(group)

    response = client.post(
        f"/api/v1/group/{group}/variant/{variant}/task/{task}",
        data=json.dumps(dict(code="main = lambda x: 42")),
        headers=dict(token="CHANGE_ME"),
        content_type='application/json'
    )

    assert response.is_json
    assert response.json['id'] == task
    assert response.json['status'] == Status.Submitted
    assert response.json['status_name'] == "Отправлено"


@mode("exam")
def test_final_submissions_are_paused(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db, TypeOfTask.Random)
    db.seeds.begin_final_test(group)
    db.seeds.end_final_test(group)

    response = client.post(
        f"/api/v1/group/{group}/variant/{variant}/task/{task}",
        data=json.dumps(dict(code="main = lambda x: 42")),
        headers=dict(token="CHANGE_ME"),
        content_type='application/json'
    )

    assert response.is_json
    assert response.json["error"] == 500
