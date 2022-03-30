from sqlalchemy.orm import Session
from tests.utils import unique_int
from tests.utils import unique_str

from webapp.repositories import TaskStatusRepository
from webapp.models import TaskStatusEnum


def test_task_status_creation(session: Session):
    ts_manager = TaskStatusRepository(session)
    ts_task = unique_int()
    ts_variant = unique_int()
    ts_group = unique_int()
    ts_code = unique_str()

    ts_manager.submit_task(ts_task, ts_variant, ts_group, ts_code)
    task_statues = ts_manager.get_all()

    ts_exists = any(task.task == ts_task and task.variant == ts_variant and
                    task.group == ts_group for task in task_statues)
    assert ts_exists


def test_task_status_fetching_by_group(session: Session):
    ts_manager = TaskStatusRepository(session)
    ts_task_1 = unique_int()
    ts_task_2 = unique_int()
    ts_variant_1 = unique_int()
    ts_variant_2 = unique_int()
    ts_group = unique_int()
    ts_code = unique_str()

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
    ts_task = unique_int()
    ts_variant = unique_int()
    ts_group = unique_int()
    ts_code = unique_str()
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
    ts_variant = unique_int()
    ts_group = unique_int()
    ts_code = unique_str()
    ts_task = unique_int()
    ts_output = unique_str()

    ts_manager.submit_task(ts_task, ts_variant, ts_group, ts_code)
    ts_status_enum = []
    ts_name_enum = []
    ts_output_list = []

    for ts_enum in TaskStatusEnum:
        if ts_enum != TaskStatusEnum.Checked:
            ts_status_enum.append(ts_enum.value)
            ts_manager.update_status(ts_task, ts_variant, ts_group, ts_enum.value, ts_output)
            ts_name = ts_manager.get_task_status(ts_task, ts_variant, ts_group)
            ts_name_enum.append(ts_name.status.value)
            ts_output_list.append(ts_name.output)

    ts_status_enum.append(TaskStatusEnum.Checked)
    ts_manager.update_status(ts_task, ts_variant, ts_group, TaskStatusEnum.Checked, ts_output)
    ts_name = ts_manager.get_task_status(ts_task, ts_variant, ts_group)
    ts_name_enum.append(ts_name.status.value)
    ts_output_list.append(ts_name.output)

    ts_output_exists = any(ts_name.output != ts_out for ts_out in ts_output_list)

    assert ts_status_enum == ts_name_enum
    assert not ts_output_exists

