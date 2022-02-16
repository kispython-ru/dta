from multiprocessing import Process
from flask import Blueprint, current_app as app
from app.managers import AppDbContext, TaskStatusEnum
from app.utils import create_session_manually
import time
import sys
import os
import traceback
from app.models import Group, Message, Task, Variant

blueprint = Blueprint('worker', __name__)


def decrypt_exception() -> str:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(
        exc_type, exc_value, exc_traceback)
    log = ''.join('!! ' + line for line in lines)
    return log


# HACK Change sys path, change os current working directory.
def check_solution(
        group: Group,
        task: Task,
        variant: Variant,
        message: Message):
    cwd = os.getcwd()
    sys.path.insert(1, os.path.join(sys.path[0], '../core'))
    os.chdir(sys.path[1])
    from check_solution import check_solution
    (ok, error) = check_solution(
        group=group.title,
        task=task.title,
        variant=variant.id - 1,
        prog=message.code)
    os.chdir(cwd)
    return (ok, error)


def process_pending_messages(db: AppDbContext):
    print('Checking for incoming messages...')
    pending_messages = db.messages.get_pending_messages_unique()
    for message in pending_messages:
        group = db.groups.get_by_id(message.group)
        task = db.tasks.get_by_id(message.task)
        variant = db.variants.get_by_id(message.variant)
        print(f'g-{message.group}, t-{message.task}, v-{message.variant}')
        try:
            (ok, error) = check_solution(group, task, variant, message)
            print(f'Check result: {ok}, {error}')
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
