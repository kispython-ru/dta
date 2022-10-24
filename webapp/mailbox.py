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


def get_senders(connection: imaplib.IMAP4_stream):
    senders = []
    _, ids = connection.search(None, '(ALL)')
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


def background_worker(login: str, password: str):
    print(f"Starting background worker for: {login}")
    while True:
        try:
            senders = get_all_senders(login, password)
            print(senders)
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
    except BaseException:
        exception = get_exception_info()
        print(f"Error occured while starting process: {exception}")
