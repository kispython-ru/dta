from sqlalchemy.orm import Session
from tests.utils import unique_id

from flask.testing import FlaskClient

from webapp.repositories import GroupRepository


def test_group_prefixes(session: Session, client: FlaskClient):
    prefix_one = "prefix_one-"
    prefix_two = "prefix_two-"
    group_manager = GroupRepository(session)
    group_manager.create_by_names([prefix_one + unique_id(), prefix_two + unique_id()])

    response = client.get("/api/v1/group/prefixes")
    assert response.is_json
    assert response.json["prefixes"] is not None
    assert "prefix_one" in response.json["prefixes"]
    assert "prefix_two" in response.json["prefixes"]
