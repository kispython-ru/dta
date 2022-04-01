from tests.utils import unique_int, unique_str

from webapp.repositories import AppDatabase


def test_message_creation(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    db.messages.submit_task(task, variant, group, code, ip)
    messages = db.messages.get_all()

    assert any(message.task == task for message in messages)


def test_message_get_latest(db: AppDatabase):
    task_1 = unique_int()
    task_2 = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()
    size = 2  # the number of recent messages we want to receive

    db.messages.submit_task(task_1, variant, group, code, ip)
    db.messages.submit_task(task_2, variant, group, code, ip)

    messages_list = db.messages.get_all()
    message_latest = messages_list[0:size]

    message = db.messages.get_latest(size)
    assert len(message) == len(message_latest)
    assert message == message_latest


def test_message_mark_at_process(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    db.messages.submit_task(task, variant, group, code, ip)
    messages = db.messages.get_all()
    message = next(mess for mess in messages if mess.task == task)
    assert message is not None
    assert message.processed == False

    db.messages.mark_as_processed(task, variant, group)

    messages = db.messages.get_all()
    message = next(mess for mess in messages if mess.task == task)
    assert message is not None
    assert message.processed == True


def test_message_get_pending(db: AppDatabase):
    task_1 = unique_int()
    task_2 = unique_int()
    task_3 = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    db.messages.submit_task(task_1, variant, group, code, ip)
    db.messages.submit_task(task_2, variant, group, code, ip)
    db.messages.submit_task(task_3, variant, group, code, ip)

    db.messages.mark_as_processed(task_2, variant, group)

    messages = db.messages.get_all()
    message_pending = list(filter(lambda m: m.processed == False, messages))
    message = db.messages.get_pending_messages()

    assert not any(mess.processed == True for mess in message)
    assert len(message) == len(message_pending)
    assert message == message_pending


def test_message_pending_unique(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    db.messages.submit_task(task, variant, group, code, ip)
    db.messages.submit_task(task, variant, group, code, ip)

    messages = db.messages.get_pending_messages_unique()
    message_count = len(list(filter(lambda m: m.task == task, messages)))
    assert message_count == 1
