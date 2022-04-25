from tests.utils import unique_int

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_variant_fetching(db: AppDatabase, client: FlaskClient):
    variant_one = unique_int()
    variant_two = unique_int()
    db.variants.create_by_ids([variant_one, variant_two])

    response = client.get("/api/v1/variant/list")

    assert response.is_json
    assert len(response.json) != 0
    assert variant_one in response.json
    assert variant_two in response.json
