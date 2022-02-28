import os

import pytest
from sqlalchemy.orm import Session

from flask import Flask

from webapp.app import configure_app
from webapp.utils import create_session_manually


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
def session(app: Flask) -> Session:
    connection_string = app.config["CONNECTION_STRING"]
    session = create_session_manually(connection_string)
    return session


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


@pytest.fixture()
def runner(app: Flask):
    return app.test_cli_runner()
