from tests.utils import unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_group_prefixes(db: AppDatabase, client: FlaskClient):
    prefix_one = "prefix_one-"
    prefix_two = "prefix_two-"
    db.groups.create_by_names([
        prefix_one + unique_str(),
        prefix_two + unique_str()
    ])

    response = client.get("/api/v1/group/prefixes")

    assert response.is_json
    assert response.json["prefixes"] is not None
    assert "prefix_one" in response.json["prefixes"]
    assert "prefix_two" in response.json["prefixes"]


def test_group_fetching(db: AppDatabase, client: FlaskClient):
    prefix_one = unique_str()
    prefix_two = unique_str()
    db.groups.create_by_names([
        prefix_one + unique_str(),
        prefix_two + unique_str(),
        prefix_one + unique_str()
    ])

    response = client.get(f"/api/v1/group/{prefix_one}")

    assert response.is_json
    assert len(response.json) == 2
    assert response.json[0]["title"].startswith(prefix_one)
    assert response.json[1]["title"].startswith(prefix_one)
