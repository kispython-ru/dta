<<<<<<< HEAD
from sqlalchemy.orm import Session
from tests.utils import unique_id_int

from webapp.repositories import TaskRepository


def test_task_creation(session: Session):
    task_manager = TaskRepository(session)
    task_name = unique_id_int()

    task_manager.create_by_ids([task_name])
    tasks = task_manager.get_all()

    tasks_exists = any(task.id == task_name for task in tasks)
    assert tasks_exists


def test_task_fetching_by_id(session: Session):
    task_manager = TaskRepository(session)
    task_name = unique_id_int()
    task_manager.create_by_ids([task_name])

    tasks = task_manager.get_all()
    task_id = next(task.id for task in tasks if task.id == task_name)

    task = task_manager.get_by_id(task_id)
    assert task.id == task_id
    assert task.id == task_name

=======
from tests.utils import unique_int

from webapp.repositories import AppDatabase


def test_task_creation(db: AppDatabase):
    task_name = unique_int()

    db.tasks.create_by_ids([task_name])
    tasks = db.tasks.get_all()

    assert any(task.id == task_name for task in tasks)


def test_task_fetching_by_id(db: AppDatabase):
    task_id = unique_int()
    db.tasks.create_by_ids([task_id])

    task = db.tasks.get_by_id(task_id)
    assert task.id == task_id
>>>>>>> b35726f53ce8266ce7990a5177021db7b8d2a3c0
