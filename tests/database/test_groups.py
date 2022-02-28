from sqlalchemy.orm import Session
from tests.utils import unique_id

from webapp.managers import GroupManager


def test_group_creation(session: Session):
    group_manager = GroupManager(session)
    group_name = unique_id()

    group_manager.create_by_names([group_name])
    groups = group_manager.get_all()

    group_exists = any(group.title == group_name for group in groups)
    assert group_exists
