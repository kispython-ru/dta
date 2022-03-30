from sqlalchemy.orm import Session
from tests.utils import unique_int

from webapp.repositories import VariantRepository


def test_variant_creation(session: Session):
    variant_manager = VariantRepository(session)
    variant_name = unique_int()

    variant_manager.create_by_ids([variant_name])
    variants = variant_manager.get_all()

    variant_exists = any(variant.id == variant_name for variant in variants)
    assert variant_exists


def test_variant_fetching_by_id(session: Session):
    variant_manager = VariantRepository(session)
    variant_name = unique_int()
    variant_manager.create_by_ids([variant_name])

    variants = variant_manager.get_all()
    variant_id = next(variant.id for variant in variants if variant.id == variant_name)

    variant = variant_manager.get_by_id(variant_name)
    assert variant.id == variant_id
    assert variant.id == variant_name
