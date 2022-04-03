from tests.utils import unique_str

from webapp.repositories import AppDatabase


def test_group_creation(db: AppDatabase):
    group_name = unique_str()
    db.groups.create_by_names([group_name])

    groups = db.groups.get_all()

    assert any(group.title == group_name for group in groups)


def test_group_fetching_by_id(db: AppDatabase):
    group_name = unique_str()
    db.groups.create_by_names([group_name])

    groups = db.groups.get_all()
    group_id = next(group.id for group in groups if group.title == group_name)
    group = db.groups.get_by_id(group_id)

    assert group.id == group_id
    assert group.title == group_name


def test_group_fetching_by_prefix(db: AppDatabase):
    prefix = "example_prefix"
    one = prefix + unique_str()
    two = prefix + unique_str()
    three = unique_str()

    db.groups.create_by_names([one, two, three])
    groups = db.groups.get_by_prefix(prefix)

    assert any(group.title == one for group in groups)
    assert any(group.title == two for group in groups)
    assert not(any(group.title == three for group in groups))
