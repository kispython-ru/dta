from tests.utils import arrange_task, unique_int, unique_str

from webapp.models import Status
from webapp.repositories import AppDatabase


def test_task_status_creation(db: AppDatabase):
    (group, variant, task) = arrange_task(db)

    db.statuses.submit_task(task, variant, group, unique_str(), unique_str())
    task_statuses = db.statuses.get_all()

    assert any(task_status.task == task for task_status in task_statuses)


def test_task_status_fetching_by_group(db: AppDatabase):
    (group, variant, task_1) = arrange_task(db)
    code = unique_str()

    task_2 = unique_int()
    db.tasks.create_by_ids([task_2])
    db.statuses.submit_task(task_1, variant, group, code, unique_str())
    db.statuses.submit_task(task_2, variant, group, code, unique_str())

    status = db.statuses.get_by_group(group)
    assert all(task.task == task_1 or task.task == task_2 for task in status)


def test_task_status_get_task_status(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    code = unique_str()
    db.statuses.submit_task(task, variant, group, code, unique_str())

    task_status = db.statuses.get_task_status(task, variant, group)
    assert task_status.task == task
    assert task_status.variant == variant
    assert task_status.group == group
    assert task_status.code == code
    assert task_status.status == Status.Submitted


def test_task_status_check_existing(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    db.statuses.submit_task(task, variant, group, unique_str(), unique_str())
    for ok, expected in [
        (False, Status.Failed),
        (False, Status.Failed),
        (True, Status.Checked),
        (False, Status.CheckedFailed),
        (True, Status.Checked),
    ]:
        db.statuses.check(task, variant, group, unique_str(), ok, unique_str(), unique_str())
        task_status = db.statuses.get_task_status(task, variant, group)
        assert task_status.status == expected


def test_task_status_check_unexisting(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    for ok, expected in [
        (False, Status.Failed),
        (False, Status.Failed),
        (True, Status.Checked),
        (False, Status.CheckedFailed),
        (True, Status.Checked),
    ]:
        db.statuses.check(task, variant, group, unique_str(), ok, unique_str(), unique_str())
        task_status = db.statuses.get_task_status(task, variant, group)
        assert task_status.status == expected
