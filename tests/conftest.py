import os
import signal

import pytest

from flask import Flask
from flask.testing import FlaskClient

from webapp.app import configure_app, configure_background_services
from webapp.commands import migrate
from webapp.repositories import AppDatabase


@pytest.fixture()
def app(request):
    param = request.param if hasattr(request, 'param') else None
    src = os.getcwd()
    tests = os.path.join(src, "tests")
    app = configure_app(tests)
    app.config.update({'WTF_CSRF_ENABLED': False})
    if param == 'enable-worker':
        app.config['DISABLE_BACKGROUND_WORKER'] = False
    if param == 'enable-registration':
        app.config["ENABLE_REGISTRATION"] = True
    if param == 'enable-exam':
        app.config['CONNECTION_STRING'] = app.config['EXAM_CONNECTION_STRING']
        migrate(app.config['CONNECTION_STRING'])
        app.config['ENABLE_REGISTRATION'] = False
        app.config['FINAL_TASKS'] = {
            "0": list(range(0, 5)),
            "1": list(range(5, 9))
        }
    app = configure_background_services(app)
    yield app
    if param == 'enable-worker':
        wpid = app.config["WORKER_PID"]
        os.kill(wpid, signal.SIGTERM)
    if param == 'enable-registration':
        mpid = app.config["MAILBOX_PID"]
        os.kill(mpid, signal.SIGTERM)


@pytest.fixture()
def db(app: Flask) -> AppDatabase:
    return AppDatabase(lambda: app.config["CONNECTION_STRING"])


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
