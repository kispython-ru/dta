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
from webapp.utils import get_exception_info


blueprint = Blueprint("mailbox", __name__)
config = AppConfigManager(lambda: app.config)


def get_messages(connection: imaplib.IMAP4_stream):
    messages = []
    _, ids = connection.search(None, '(ALL)')
    for i in ids[0].decode('utf-8').split():
        _, data = connection.fetch(i, '(BODY[HEADER.FIELDS (FROM BCC)])')
        try:
            string = data[0][1].decode('utf-8')
            message = email.message_from_string(string)
            sender = email.utils.parseaddr(message["From"])[1]
            print(f'{sender}')
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured while procedding message: {exception}")
    return messages


def process_pending_mails(login: str, password: str):
    with imaplib.IMAP4_SSL('imap.yandex.ru') as connection:
        connection.login(login, password)
        messages = []
        connection.select('INBOX')
        messages += get_messages(connection)
        connection.select('Spam')
        messages += get_messages(connection)


def background_worker(login: str, password: str):
    print(f"Starting background worker for: {login}")
    while True:
        try:
            process_pending_mails(login, password)
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured inside the loop: {exception}")
        time.sleep(10)


@blueprint.before_app_first_request
def start_background_worker():
    if not config.config.enable_registration:
        return
    login = config.config.smtp_login
    password = config.config.smtp_password
    process = Process(target=background_worker, args=(login, password))
    try:
        process.start()
        app.config["WORKER_PID"] = process.pid
    except BaseException:
        exception = get_exception_info()
        print(f"Error occured while starting process: {exception}")
