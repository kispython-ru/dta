from sqlalchemy.orm import Session
from tests.utils import unique_int
from tests.utils import unique_str

from webapp.repositories import MessageRepository


def test_message_creation(session: Session):
    message_manager = MessageRepository(session)
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    message_manager.submit_task(task, variant, group, code, ip)
    messages = message_manager.get_all()

    message_exists = any(message.task == task and message.variant == variant and
                         message.group == group for message in messages)
    assert message_exists


def test_message_get_latest(session: Session):
    message_manager = MessageRepository(session)
    task_1 = unique_int()
    task_2 = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()
    size = 2  # the number of recent messages we want to receive

    message_manager.submit_task(task_1, variant, group, code, ip)
    message_manager.submit_task(task_2, variant, group, code, ip)

    messages = message_manager.get_all()
    message_latest = messages[0:size]

    message = message_manager.get_latest(size)
    assert len(message) == len(message_latest)
    assert message == message_latest


def test_message_mark_at_process(session: Session):
    message_manager = MessageRepository(session)
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    message_manager.submit_task(task, variant, group, code, ip)
    messages = message_manager.get_all()
    message_name = next(message for message in messages if message.task == task and
                        message.variant == variant and message.group == group)
    assert message_name is not None
    assert message_name.processed == False

    message_manager.mark_as_processed(task, variant, group)

    messages = message_manager.get_all()
    message_name = next(message for message in messages if message.task == task and
                        message.variant == variant and message.group == group)
    assert message_name is not None
    assert message_name.processed == True


def test_message_get_pending(session: Session):
    message_manager = MessageRepository(session)
    task_1 = unique_int()
    task_2 = unique_int()
    task_3 = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    message_manager.submit_task(task_1, variant, group, code, ip)
    message_manager.submit_task(task_2, variant, group, code, ip)
    message_manager.submit_task(task_3, variant, group, code, ip)

    message_manager.mark_as_processed(task_2, variant, group)

    messages = message_manager.get_all()
    message_name = list(filter(lambda m: m.processed == False, messages))
    message = message_manager.get_pending_messages()
    true_exists = any(message.processed == True for message in message)

    assert not true_exists
    assert len(message) == len(message_name)
    assert message == message_name


def test_message_pending_unique(session: Session):
    message_manager = MessageRepository(session)
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    ip = unique_str()

    message_manager.submit_task(task, variant, group, code, ip)
    message_manager.submit_task(task, variant, group, code, ip)

    messages = message_manager.get_pending_messages_unique()
    message_count = len(list(filter(lambda m: m.task == task, messages)))
    assert message_count == 1
