import os
import signal

import pytest

from flask import Flask
from flask.testing import FlaskClient

from webapp.app import configure_app
from webapp.repositories import AppDatabase


@pytest.fixture()
def app(request) -> Flask:
    src = os.getcwd()
    tests = os.path.join(src, "tests")
    app = configure_app(tests)
    enable_worker = hasattr(request, 'param') and request.param is True
    if enable_worker:
        app.config["DISABLE_BACKGROUND_WORKER"] = False
    yield app
    if enable_worker:
        worker_pid = app.config["WORKER_PID"]
        os.kill(worker_pid, signal.SIGTERM)


@pytest.fixture()
def db(app: Flask) -> AppDatabase:
    return AppDatabase(lambda: app.config["CONNECTION_STRING"])


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
