import sys
import time
from multiprocessing import Process

from webapp.dto import AppConfig
from webapp.managers import ExternalTaskManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info


def check_solution(
    core_path: str,
    group_title: str,
    task: int,
    variant: int,
    code: str
):
    if core_path not in sys.path:
        sys.path.insert(1, core_path)
    from check_solution import check_solution
    (ok, error) = check_solution(
        group=group_title,
        task=task,
        variant=variant,
        code=code,
    )
    return (ok, error)


def load_config(core_path: str):
    if core_path not in sys.path:
        sys.path.insert(1, core_path)
    from check_solution import load_config
    return load_config()


def analyze_solution(analytics_path: str, task: int, code: str):
    if analytics_path not in sys.path:
        sys.path.insert(1, analytics_path)
    from analyze_solution import analyze_solution
    return analyze_solution(task, code)


def process_pending_messages(config: AppConfig, db: AppDatabase, external: ExternalTaskManager):
    pending_messages = db.messages.get_pending_messages()
    message_count = len(pending_messages)
    if message_count == 0:
        return
    print(f"Processing {message_count} incoming messages...")
    for message in pending_messages:
        group = db.groups.get_by_id(message.group)
        variant = db.variants.get_by_id(message.variant)
        task = db.tasks.get_by_id(message.task)
        seed = db.seeds.get_final_seed(group.id)
        ext = external.get_external_task(group, variant, task, seed, config)
        print(f"g-{message.group}, t-{message.task}, v-{message.variant}")
        print(f"external: {ext.group_title}, t-{ext.task}, v-{ext.variant}")
        try:
            ok, error = check_solution(
                core_path=config.core_path,
                group_title=ext.group_title,
                task=ext.task,
                variant=ext.variant,
                code=message.code,
            )
            print(f"Check result: {ok}, {error}")
            status = db.statuses.check(
                task=message.task,
                variant=message.variant,
                group=message.group,
                code=message.code,
                ok=ok,
                output=error,
                ip=message.ip,
            )
            db.messages.mark_as_processed(message.id)
            check = db.checks.record_check(message.id, status.status, error)
            if not ok:
                continue
            analyzed, order = analyze_solution(
                analytics_path=config.analytics_path,
                code=message.code,
                task=ext.task,
            )
            print(f'Analysis result: {analyzed}, {order}')
            if not analyzed:
                continue
            db.checks.record_achievement(
                check=check.id,
                achievement=order
            )
            db.statuses.record_achievement(
                task=message.task,
                variant=message.variant,
                group=message.group,
                achievement=order,
            )
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured while checking for messages: {exception}")


def background_worker(config: AppConfig):
    print(f"Starting background worker for database: {config.connection_string}")
    db = AppDatabase(lambda: config.connection_string)
    ext = ExternalTaskManager(db.groups, db.tasks)
    while True:
        try:
            process_pending_messages(config, db, ext)
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured inside the loop: {exception}")
        time.sleep(10)


def start_background_worker(config: AppConfig):
    if config.no_background_worker:
        return
    process = Process(target=background_worker, args=(config,))
    try:
        process.start()
        return process.pid
    except Exception as e:
        print(e)
