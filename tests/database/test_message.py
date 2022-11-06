from tests.utils import arrange_task, unique_int, unique_str

from webapp.repositories import AppDatabase


def test_message_creation(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    code = unique_str()
    ip = unique_str()

    db.messages.submit_task(task, variant, group, code, ip, None)
    messages = db.messages.get_all()

    assert any(message.task == task for message in messages)


def test_message_get_latest(db: AppDatabase):
    (group, variant, task_1) = arrange_task(db)
    code = unique_str()
    ip = unique_str()

    task_2 = unique_int()
    db.tasks.create_by_ids([task_2])
    db.messages.submit_task(task_1, variant, group, code, ip, None)
    db.messages.submit_task(task_2, variant, group, code, ip, None)

    latest = db.messages.get_latest(2)
    assert len(latest) == 2


def test_message_mark_at_process(db: AppDatabase):
    (group, variant, task) = arrange_task(db)
    code = unique_str()
    ip = unique_str()

    db.messages.submit_task(task, variant, group, code, ip, None)
    messages = db.messages.get_all()
    message = next(mess for mess in messages if mess.task == task)
    assert message is not None
    assert not message.processed

    db.messages.mark_as_processed(message.id)

    messages = db.messages.get_all()
    message = next(mess for mess in messages if mess.task == task)
    assert message is not None
    assert message.processed


def test_message_get_pending(db: AppDatabase):
    (group, variant, task_1) = arrange_task(db)
    code = unique_str()
    ip = unique_str()

    task_2 = unique_int()
    task_3 = unique_int()
    db.tasks.create_by_ids([task_2, task_3])

    message = db.messages.submit_task(task_1, variant, group, code, ip, None)
    db.messages.mark_as_processed(message.id)

    messages = db.messages.get_all()
    pending = list(filter(lambda m: not m.processed, messages))
    messages = db.messages.get_pending_messages()

    assert not any(mess.processed for mess in messages)
    assert len(messages) == len(pending)
    assert messages[-1].code == pending[0].code
