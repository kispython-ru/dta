<<<<<<< HEAD
from sqlalchemy.orm import Session
from tests.utils import unique_id_int

from webapp.repositories import VariantRepository


def test_variant_creation(session: Session):
    variant_manager = VariantRepository(session)
    variant_name = unique_id_int()

    variant_manager.create_by_ids([variant_name])
    variants = variant_manager.get_all()

    variant_exists = any(variant.id == variant_name for variant in variants)
    assert variant_exists


def test_variant_fetching_by_id(session: Session):
    variant_manager = VariantRepository(session)
    variant_name = unique_id_int()
    variant_manager.create_by_ids([variant_name])

    variants = variant_manager.get_all()
    variant_id = next(variant.id for variant in variants if variant.id == variant_name)

    variant = variant_manager.get_by_id(variant_name)
    assert variant.id == variant_id
    assert variant.id == variant_name
=======
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
>>>>>>> b35726f53ce8266ce7990a5177021db7b8d2a3c0
