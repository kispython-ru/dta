import pytest

from webapp.app import create_app


@pytest.fixture()
def app():
    # TODO: create app with `TEST` settings
    app = create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
