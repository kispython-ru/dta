import copy
import time

from sqlalchemy.orm import Session
from tests.utils import unique_id_int
from tests.utils import unique_id

from webapp.repositories import MessageRepository


def test_message_creation(session: Session):
    message_manager = MessageRepository(session)
    m_task = unique_id_int()
    m_variant = unique_id_int()
    m_group = unique_id_int()
    m_code = unique_id()
    m_ip = unique_id()

    message_manager.submit_task(m_task, m_variant, m_group, m_code, m_ip)
    messages = message_manager.get_all()

    message_exists = any(message.task == m_task and message.variant == m_variant and
                         message.group == m_group for message in messages)
    assert message_exists


def test_message_get_latest(session: Session):
    message_manager = MessageRepository(session)
    m_task_1 = unique_id_int()
    m_task_2 = unique_id_int()
    m_variant = unique_id_int()
    m_group = unique_id_int()
    m_code = unique_id()
    m_ip = unique_id()
    m_size = 2

    message_manager.submit_task(m_task_1, m_variant, m_group, m_code, m_ip)
    message_manager.submit_task(m_task_2, m_variant, m_group, m_code, m_ip)

    messages = message_manager.get_all()
    message_latest = messages[0:m_size]

    message = message_manager.get_latest(m_size)
    assert len(message) == len(message_latest)
    assert message == message_latest


def test_message_mark_at_process(session: Session):
    message_manager = MessageRepository(session)
    m_task = unique_id_int()
    m_variant = unique_id_int()
    m_group = unique_id_int()
    m_code = unique_id()
    m_ip = unique_id()

    message_manager.submit_task(m_task, m_variant, m_group, m_code, m_ip)
    message_manager.mark_as_processed(m_task, m_variant, m_group)

    messages = message_manager.get_all()
    message_name = next(message for message in messages if message.task == m_task and
                        message.variant == m_variant and message.group == m_group)

    assert message_name.processed == True


def test_message_get_pending(session: Session):
    message_manager = MessageRepository(session)
    m_task_1 = unique_id_int()
    m_task_2 = unique_id_int()
    m_task_3 = unique_id_int()
    m_variant = unique_id_int()
    m_group = unique_id_int()
    m_code = unique_id()
    m_ip = unique_id()

    message_manager.submit_task(m_task_1, m_variant, m_group, m_code, m_ip)
    message_manager.submit_task(m_task_2, m_variant, m_group, m_code, m_ip)
    message_manager.submit_task(m_task_3, m_variant, m_group, m_code, m_ip)

    message_manager.mark_as_processed(m_task_2, m_variant, m_group)

    messages = iter(message_manager.get_all())
    messages_copy = copy.copy(messages)
    message_name = []
    while any(mess.processed == False for mess in messages):
        message_name.append(next(mess for mess in messages_copy if mess.processed == False))

    true_exists = any(message.processed == True for message in messages)

    message = message_manager.get_pending_messages()
    assert not true_exists
    assert len(message) == len(message_name)
    assert message == message_name


def test_message_pending_unique(session: Session):
    message_manager = MessageRepository(session)
    m_task = unique_id_int()
    m_variant = unique_id_int()
    m_group = unique_id_int()
    m_code = unique_id()
    m_ip = unique_id()

    message_manager.submit_task(m_task, m_variant, m_group, m_code, m_ip)
    message_manager.submit_task(m_task, m_variant, m_group, m_code, m_ip)

    messages = iter(message_manager.get_pending_messages_unique())
    messages_copy = copy.copy(messages)
    message_name = []
    while any(mess.processed == False and mess.task == m_task and
              mess.variant == m_variant and mess.group == m_group
              for mess in messages):
        message_name.append(next(mess for mess in messages_copy if mess.processed == False and
                                 mess.task == m_task and mess.variant == m_variant and
                                 mess.group == m_group))

    assert len(message_name) == 1
