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
