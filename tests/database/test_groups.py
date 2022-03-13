from sqlalchemy.orm import Session
from tests.utils import unique_id

from webapp.repositories import GroupRepository


def test_group_creation(session: Session):
    group_manager = GroupRepository(session)
    group_name = unique_id()

    group_manager.create_by_names([group_name])
    groups = group_manager.get_all()

    group_exists = any(group.title == group_name for group in groups)
    assert group_exists


def test_group_fetching_by_id(session: Session):
    group_manager = GroupRepository(session)
    group_name = unique_id()
    group_manager.create_by_names([group_name])

    groups = group_manager.get_all()
    group_id = next(group.id for group in groups if group.title == group_name)

    group = group_manager.get_by_id(group_id)
    assert group.id == group_id
    assert group.title == group_name


def test_group_fetching_by_prefix(session: Session):
    prefix = "example_prefix"
    one = prefix + unique_id()
    two = prefix + unique_id()
    three = unique_id()

    group_manager = GroupRepository(session)
    group_manager.create_by_names([one, two, three])
    groups = group_manager.get_by_prefix(prefix)

    assert any(group.title == one for group in groups)
    assert any(group.title == two for group in groups)
    assert not(any(group.title == three for group in groups))
