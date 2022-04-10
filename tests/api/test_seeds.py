from tests.utils import arrange_task

from flask.testing import FlaskClient

from webapp.models import TaskStatusEnum
from webapp.repositories import AppDatabase


def test_final_seed_is_not_used(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)
    group_title = db.groups.get_by_id(group).title

    default_template = f'/{task}/{group_title}.html#вариант-{variant + 1}'
    response = client.get(f"/api/v1/group/{group}/variant/{variant}/task/{task}")

    assert response.is_json
    assert response.json['id'] == task
    assert default_template in response.json['source']
    assert response.json['status'] == TaskStatusEnum.NotSubmitted
    assert response.json['status_name'] == "Не отправлено"


def test_final_seed_is_used(db: AppDatabase, client: FlaskClient):
    (group, variant, task) = arrange_task(db)
    group_title = db.groups.get_by_id(group).title
    db.seeds.begin_final_test(group)

    default_template = f'/{task}/{group_title}.html#вариант-{variant + 1}'
    response = client.get(f"/api/v1/group/{group}/variant/{variant}/task/{task}")

    assert response.is_json
    assert response.json['id'] == task
    assert default_template not in response.json['source']
    assert response.json['status'] == TaskStatusEnum.NotSubmitted
    assert response.json['status_name'] == "Не отправлено"
