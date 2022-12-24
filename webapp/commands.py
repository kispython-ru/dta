import os
from argparse import ArgumentParser
from typing import Any, Callable

import webapp.worker as worker
from alembic import command
from alembic.config import Config
from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import load_config_files


def migrate(connection_string: str):
    base = os.path.dirname(os.path.abspath(__file__))
    ini = os.path.join(base, "alembic.ini")
    script = os.path.join(base, "alembic")
    config = Config(ini)
    config.set_main_option("sqlalchemy.url", connection_string)
    if script is not None:
        config.set_main_option("script_location", script)
    command.upgrade(config, "head")


class CmdManager:
    def __init__(self, dir: str, cmds: list[Callable[[str], Any]]):
        self.runners = dict()
        self.parser = ArgumentParser()
        self.dir = dir
        for cmd in cmds:
            runner = cmd()
            key = runner.command.strip('-')
            self.runners[key] = runner
            self.parser.add_argument(
                runner.command,
                help=runner.help,
                required=False,
                action='store_true'
            )

    def run(self):
        args = self.parser.parse_args()
        for key, active in vars(args).items():
            if not active:
                continue
            self.runners[key].run(self.dir)


class SeedCmd:
    def __init__(self):
        self.command = "--seed"
        self.help = "seeds the database using core"

    def run(self, dir: str):
        config = AppConfigManager(lambda: load_config_files(dir)).config
        print(f'Seeding db {config.connection_string} using core {config.core_path}...')
        groups, tasks = worker.load_tests(config.core_path)
        migrate(config.connection_string)
        db = AppDatabase(lambda: config.connection_string)
        db.groups.delete_all()
        db.tasks.delete_all()
        db.variants.delete_all()
        db.groups.create_by_names(groups)
        db.tasks.create_by_ids(tasks)
        db.variants.create_by_ids(range(0, 39 + 1))
        print(f'Done seeing db {config.connection_string} using core {config.core_path}!')


class AnalyzeCmd:
    def __init__(self):
        self.command = "--analyze"
        self.help = "evaluates analytics for all accepted programs"

    def run(self, dir: str):
        config = AppConfigManager(lambda: load_config_files(dir)).config
        db = AppDatabase(lambda: config.connection_string)
        db.statuses.clear_achievements()
        checked = db.checks.checked()
        print(f'Cleared achievements, analyzing {len(checked)} checked programs...')
        for status in checked:
            message = db.messages.get_by_id(status.message)
            analyzed, achievement = worker.analyze_solution(
                analytics_path=config.analytics_path,
                code=message.code,
                task=message.task,
            )
            if not analyzed:
                continue
            db.statuses.record_achievement(
                task=message.task,
                variant=message.variant,
                group=message.group,
                achievement=achievement,
            )
        print(f'Done analyzing {len(checked)} programs.')
