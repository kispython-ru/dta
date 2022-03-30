from tests.utils import unique_int, unique_str

from webapp.repositories import AppDatabase
from webapp.models import TaskStatusEnum


def test_creation(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()

    db.statuses.submit_task(task, variant, group, code)
    task_statuses = db.statuses.get_all()

    assert any(task_status.task == task for task_status in task_statuses)


def test_fetching_by_group(db: AppDatabase):
    task_1 = unique_int()
    task_2 = unique_int()
    variant_1 = unique_int()
    variant_2 = unique_int()
    group = unique_int()
    code = unique_str()

    db.statuses.submit_task(task_1, variant_1, group, code)
    db.statuses.submit_task(task_2, variant_2, group, code)

    task_statuses = iter(db.statuses.get_all())
    ts_by_group = [next(ts for ts in task_statuses if ts.group == group),
                   next(ts for ts in task_statuses if ts.group == group)]

    task_status = db.statuses.get_by_group(group)
    assert len(task_status) == len(ts_by_group)
    assert task_status == ts_by_group


def test_get_task_status(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    db.statuses.submit_task(task, variant, group, code)

    task_statuses = db.statuses.get_all()
    ts_name = next(ts for ts in task_statuses if ts.task == task)

    task_status = db.statuses.get_task_status(task, variant, group)
    assert task_status == ts_name
    assert task_status.task == task
    assert task_status.variant == variant
    assert task_status.group == group


def test_update_status(db: AppDatabase):
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    task = unique_int()
    output = unique_str()

    db.statuses.submit_task(task, variant, group, code)
    status_enum = []
    name_enum = []
    output_list = []

    for ts_enum in TaskStatusEnum:
        if ts_enum != TaskStatusEnum.Checked:
            status_enum.append(ts_enum.value)
            db.statuses.update_status(task, variant, group, ts_enum.value, output)
            task_status = db.statuses.get_task_status(task, variant, group)
            name_enum.append(task_status.status.value)
            output_list.append(task_status.output)

    status_enum.append(TaskStatusEnum.Checked)
    db.statuses.update_status(task, variant, group, TaskStatusEnum.Checked, output)
    task_status = db.statuses.get_task_status(task, variant, group)
    name_enum.append(task_status.status.value)
    output_list.append(task_status.output)

    assert status_enum == name_enum
    assert not any(task_status.output != ts_output for ts_output in output_list)
