import email
import email.header
import email.message
import email.utils
import imaplib
import time
from multiprocessing import Process

from flask import Blueprint
from flask import current_app as app

from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info


blueprint = Blueprint("mailbox", __name__)
config = AppConfigManager(lambda: app.config)


def get_senders(connection: imaplib.IMAP4_stream):
    senders = []
    _, ids = connection.search(None, '(UNSEEN)')
    for i in ids[0].decode('utf-8').split():
        _, data = connection.fetch(i, '(BODY[HEADER.FIELDS (FROM)])')
        try:
            string = data[0][1].decode('utf-8')
            message = email.message_from_string(string)
            _, sender = email.utils.parseaddr(message["From"])
            senders.append(sender)
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured while procedding message: {exception}")
    return senders


def get_all_senders(login: str, password: str):
    with imaplib.IMAP4_SSL('imap.yandex.ru') as connection:
        connection.login(login, password)
        messages = []
        connection.select('INBOX')
        messages += get_senders(connection)
        connection.select('Spam')
        messages += get_senders(connection)
        return messages


def background_worker(login: str, password: str, connection: str):
    print(f"Starting background worker for IMAP {login} and database: {connection}")
    db = AppDatabase(lambda: connection)
    while True:
        try:
            senders = get_all_senders(login, password)
            length = len(senders)
            if length:
                print(f'Received {length} emails! Processing...')
                for email in senders:
                    if db.students.find_by_email(email):
                        db.students.confirm(email)
                print(f'Successfully processed {length} emails.')
        except ConnectionResetError:
            print(f'IMAP connection has been reset, reconnecting...')
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured inside the loop: {exception}")
        time.sleep(10)


@blueprint.before_app_first_request
def start_background_worker():
    if not config.config.enable_registration:
        return
    process = Process(target=background_worker, args=(
        config.config.smtp_login,
        config.config.smtp_password,
        config.config.connection_string
    ))
    try:
        process.start()
    except BaseException:
        exception = get_exception_info()
        print(f"Error occured while starting process: {exception}")
