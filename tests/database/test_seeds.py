from tests.utils import unique_int, unique_str

from webapp.repositories import AppDatabase


def test_final_seed_is_empty(db: AppDatabase):
    identity = unique_int()
    seed = db.seeds.get_final_seed(identity)
    assert seed is None


def test_final_seed_is_not_empty(db: AppDatabase):
    group_name = unique_str()
    db.groups.create_by_names([group_name])
    group = db.groups.get_by_prefix(group_name)[0]

    db.seeds.begin_final_test(group.id)
    seed = db.seeds.get_final_seed(group.id)

    assert seed is not None
    assert seed.group == group.id
    assert seed.active == True


def test_final_test_is_finished(db: AppDatabase):
    group_name = unique_str()
    db.groups.create_by_names([group_name])
    group = db.groups.get_by_prefix(group_name)[0]

    db.seeds.begin_final_test(group.id)
    db.seeds.end_final_test(group.id)
    seed = db.seeds.get_final_seed(group.id)

    assert seed is not None
    assert seed.group == group.id
    assert seed.active == False
