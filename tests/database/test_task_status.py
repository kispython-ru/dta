<<<<<<< HEAD
from sqlalchemy.orm import Session
from tests.utils import unique_id_int
from tests.utils import unique_id

from webapp.repositories import TaskStatusRepository


def test_task_status_creation(session: Session):
    ts_manager = TaskStatusRepository(session)
    ts_task = unique_id_int()
    ts_variant = unique_id_int()
    ts_group = unique_id_int()
    ts_code = unique_id()

    ts_manager.submit_task(ts_task, ts_variant, ts_group, ts_code)
    task_statues = ts_manager.get_all()

    ts_exists = any(task.task == ts_task and task.variant == ts_variant and
                    task.group == ts_group for task in task_statues)
    assert ts_exists


def test_task_status_fetching_by_group(session: Session):
    ts_manager = TaskStatusRepository(session)
    ts_task_1 = unique_id_int()
    ts_task_2 = unique_id_int()
    ts_variant_1 = unique_id_int()
    ts_variant_2 = unique_id_int()
    ts_group = unique_id_int()
    ts_code = unique_id()

    ts_manager.submit_task(ts_task_1, ts_variant_1, ts_group, ts_code)
    ts_manager.submit_task(ts_task_2, ts_variant_2, ts_group, ts_code)

    task_statuses = iter(ts_manager.get_all())
    ts_by_group = [next(ts for ts in task_statuses if ts.group == ts_group),
                   next(ts for ts in task_statuses if ts.group == ts_group)]

    task_status = ts_manager.get_by_group(ts_group)
    assert len(task_status) == len(ts_by_group)
    assert task_status == ts_by_group


def test_get_task_status(session: Session):
    ts_manager = TaskStatusRepository(session)
    ts_task = unique_id_int()
    ts_variant = unique_id_int()
    ts_group = unique_id_int()
    ts_code = unique_id()
    ts_manager.submit_task(ts_task, ts_variant, ts_group, ts_code)

    task_statuses = ts_manager.get_all()
    ts_name = next(ts for ts in task_statuses if ts.task == ts_task and
                   ts.variant == ts_variant and ts.group == ts_group)

    task_status = ts_manager.get_task_status(ts_task, ts_variant, ts_group)
    assert ts_name == task_status
    assert task_status.task == ts_task
    assert task_status.variant == ts_variant
    assert task_status.group == ts_group


def test_update_status(session: Session):
    ts_manager = TaskStatusRepository(session)
    ts_status = 1
    ts_task = unique_id_int()
    ts_variant = unique_id_int()
    ts_group = unique_id_int()
    ts_code = unique_id()
    ts_output = unique_id()

    ts_manager.submit_task(ts_task, ts_variant, ts_group, ts_code)
    ts_manager.update_status(ts_task, ts_variant, ts_group, ts_status, ts_output)

    task_statuses = ts_manager.get_all()
    ts_name = next(ts for ts in task_statuses if ts.task == ts_task and
                   ts.variant == ts_variant and ts.group == ts_group)

    assert ts_name.status == ts_status
    assert ts_name.output == ts_output
=======
from tests.utils import arrange_task, unique_int, unique_str

from webapp.models import TaskStatusEnum
from webapp.repositories import AppDatabase


def test_task_status_creation(db: AppDatabase):
    (group, variant, task) = arrange_task(db)

    db.statuses.submit_task(task, variant, group, unique_str())
    task_statuses = db.statuses.get_all()

    assert any(task_status.task == task for task_status in task_statuses)


def test_task_status_fetching_by_group(db: AppDatabase):
    (group, variant, task_1) = arrange_task(db)
    code = unique_str()

    task_2 = unique_int()
    db.tasks.create_by_ids([task_2])
    db.statuses.submit_task(task_1, variant, group, code)
    db.statuses.submit_task(task_2, variant, group, code)

    task_status = db.statuses.get_by_group(group)
    assert all([task.task == task_1 or task.task == task_2 for task in task_status])


def test_task_status_get_task_status(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    code = unique_str()
    db.statuses.submit_task(task, variant, group, code)

    task_status = db.statuses.get_task_status(task, variant, group)
    assert task_status.task == task
    assert task_status.variant == variant
    assert task_status.group == group
    assert task_status.code == code
    assert task_status.status == TaskStatusEnum.Submitted


def test_task_status_update_status(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    db.statuses.submit_task(task, variant, group, unique_str())

    for ts_enum in TaskStatusEnum:
        if ts_enum != TaskStatusEnum.Checked:
            db.statuses.update_status(task, variant, group, ts_enum.value, unique_str())
            task_status = db.statuses.get_task_status(task, variant, group)
            assert task_status.status == ts_enum.value

    db.statuses.update_status(task, variant, group, TaskStatusEnum.Checked, unique_str())
    task_status = db.statuses.get_task_status(task, variant, group)
    assert task_status.status == TaskStatusEnum.Checked
>>>>>>> b35726f53ce8266ce7990a5177021db7b8d2a3c0

