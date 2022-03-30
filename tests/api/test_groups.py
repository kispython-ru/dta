from sqlalchemy.orm import Session
from tests.utils import unique_int, unique_str

from flask.testing import FlaskClient

from webapp.repositories import GroupRepository, VariantRepository


def test_group_prefixes(session: Session, client: FlaskClient):
    prefix_one = "prefix_one-"
    prefix_two = "prefix_two-"
    group_manager = GroupRepository(session)
    group_manager.create_by_names([
        prefix_one + unique_str(),
        prefix_two + unique_str()
    ])

    response = client.get("/api/v1/group/prefixes")

    assert response.is_json
    assert response.json["prefixes"] is not None
    assert "prefix_one" in response.json["prefixes"]
    assert "prefix_two" in response.json["prefixes"]


def test_group_fetching(session: Session, client: FlaskClient):
    prefix_one = unique_str()
    prefix_two = unique_str()
    group_manager = GroupRepository(session)
    group_manager.create_by_names([
        prefix_one + unique_str(),
        prefix_two + unique_str(),
        prefix_one + unique_str()
    ])

    response = client.get(f"/api/v1/group/{prefix_one}")

    assert response.is_json
    assert len(response.json) == 2
    assert response.json[0]["title"].startswith(prefix_one)
    assert response.json[1]["title"].startswith(prefix_one)


def test_variant_fetching(session: Session, client: FlaskClient):
    variant_one = unique_int()
    variant_two = unique_int()
    variant_manager = VariantRepository(session)
    variant_manager.create_by_ids([variant_one, variant_two])

    response = client.get("/api/v1/variant/list")

    assert response.is_json
    assert len(response.json) != 0
    assert variant_one in response.json
    assert variant_two in response.json
