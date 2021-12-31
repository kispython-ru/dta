from app.app import create_app
import pytest


@pytest.fixture(scope="module")
def app():
    app = create_app()
    return app
