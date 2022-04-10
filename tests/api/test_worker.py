import json
import time
import os

import pytest
from tests.utils import arrange_task, timeout_assert

from flask import Flask
from flask.testing import FlaskClient

from webapp.models import TaskStatusEnum
from webapp.repositories import AppDatabase


@pytest.mark.skipif(os.name == 'nt', reason="not supported on Windows")
@pytest.mark.parametrize('app', ([True]), indirect=True)
def test_background_task_check(db: AppDatabase, client: FlaskClient, app: Flask):
    (group, variant, task) = arrange_task(db)
    url = f"/api/v1/group/{group}/variant/{variant}/task/{task}"

    response = client.post(
        url,
        data=json.dumps(dict(code="main = lambda x: 42")),
        headers=dict(token="CHANGE_ME"),
        content_type='application/json'
    )

    assert response.json["status"] == TaskStatusEnum.Submitted
    timeout_assert(lambda: client.get(url).json["status"] == TaskStatusEnum.Failed)
