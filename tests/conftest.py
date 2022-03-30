import os

import pytest

from flask import Flask
from flask.testing import FlaskClient

from webapp.app import configure_app
from webapp.repositories import AppDatabase


@pytest.fixture()
def app() -> Flask:
    src = os.getcwd()
    tests = os.path.join(src, "tests")
    app = configure_app(
        config_path=tests,
        alembic_ini_path="webapp/alembic.ini",
        alembic_script_path="webapp/alembic",
    )
    yield app


@pytest.fixture()
def db(app: Flask) -> AppDatabase:
    connection_string = app.config["CONNECTION_STRING"]
    db = AppDatabase(lambda: connection_string)
    return db


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def runner(app: Flask):
    return app.test_cli_runner()
