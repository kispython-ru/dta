from tests.utils import unique_int

from webapp.repositories import AppDatabase


def test_variant_creation(db: AppDatabase):
    variant_id = unique_int()

    db.variants.create_by_ids([variant_id])
    variants = db.variants.get_all()

    assert any(variant.id == variant_id for variant in variants)


def test_variant_fetching_by_id(db: AppDatabase):
    variant_id = unique_int()
    db.variants.create_by_ids([variant_id])

    variant = db.variants.get_by_id(variant_id)
    assert variant.id == variant_id
