from multiprocessing import Process
from flask import Blueprint, current_app as app
from app.managers import AppDbContext, TaskStatusEnum
from app.utils import create_session_manually
import time
import sys
import os
import traceback

blueprint = Blueprint('worker', __name__)


def decrypt_exception() -> str:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(
        exc_type, exc_value, exc_traceback)
    log = ''.join('!! ' + line for line in lines)
    return log


def process_pending_messages(db: AppDbContext):
    print('Checking for incoming messages...')
    pending_messages = db.messages.get_pending_messages_unique()
    for message in pending_messages:
        print(f'g-{message.group}, t-{message.task}, v-{message.variant}')
        try:
            # HACK Change sys path, change os current working directory.
            cwd = os.getcwd()
            sys.path.insert(1, os.path.join(sys.path[0], '../core'))
            os.chdir(sys.path[1])
            from check_solution import check_solution
            (ok, error) = check_solution(
                group=message.group,
                task=message.task,
                variant=message.variant,
                prog=message.code)
            # HACK Change the current directory back.
            os.chdir(cwd)
            print(
                f'g-{message.group}, t-{message.task}, v-{message.variant}: {ok}, {error}')
            status = TaskStatusEnum.Checked if ok else TaskStatusEnum.Failed
            db.messages.mark_as_processed(
                task=message.task,
                variant=message.variant,
                group=message.group)
            db.statuses.update_status(
                task=message.task,
                variant=message.variant,
                group=message.group,
                status=status,
                output=error)
        except BaseException:
            exception = decrypt_exception()
            print(f'Error orccured: {exception}')


def background_worker(connection_string: str):
    print(f'Starting background worker for database: {connection_string}')
    while True:
        time.sleep(10)
        with create_session_manually(connection_string) as session:
            db = AppDbContext(session)
            try:
                process_pending_messages(db)
            except BaseException:
                exception = decrypt_exception()
                print(f'Error orccured inside the loop: {exception}')


@blueprint.before_app_first_request
def start_background_worker():
    connection_string = app.config['CONNECTION_STRING']
    process = Process(target=background_worker, args=(connection_string,))
    process.start()
