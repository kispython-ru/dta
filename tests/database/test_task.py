from tests.utils import unique_int

from webapp.repositories import AppDatabase


def test_task_creation(db: AppDatabase):
    task_name = unique_int()

    db.tasks.create_by_ids([task_name])
    tasks = db.tasks.get_all()

    assert any(task.id == task_name for task in tasks)


def test_task_fetching_by_id(db: AppDatabase):
    task_name = unique_int()
    db.tasks.create_by_ids([task_name])

    tasks = db.tasks.get_all()
    task_id = next(task.id for task in tasks if task.id == task_name)

    task = db.tasks.get_by_id(task_id)
    assert task.id == task_id
    assert task.id == task_name

