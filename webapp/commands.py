from argparse import ArgumentParser
from typing import Any, Callable

import webapp.worker as worker
from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import load_config_files
import os


class CmdManager:
    def __init__(self, dir: str, commands: list[Callable[[str], Any]]):
        self.runners: dict[str, Any] = dict()
        self.parser = ArgumentParser()
        self.dir = dir
        for cmd in commands:
            runner = cmd()
            key = runner.command.strip('-')
            self.runners[key] = runner
            self.parser.add_argument(
                runner.command,
                help=runner.help,
                required=False,
                action='store_true'
            )

    def run(self) -> bool:
        args = self.parser.parse_args()
        executed = False
        for key, enabled in vars(args).items():
            if not enabled:
                continue
            print(f'Running {key} cmd')
            runner = self.runners[key]
            runner.run(self.dir)
            executed = True
        return executed


class SeedCmd:
    def __init__(self):
        self.command = "--seed"
        self.help = "seeds the database using core"

    def run(self, dir: str):
        manager = AppConfigManager(lambda: load_config_files(dir))
        connection = manager.config.connection_string
        core = manager.config.core_path
        print(f'Seeding db {connection} using core {core}...')
        groups, tasks = worker.load_tests(core)
        db = AppDatabase(lambda: connection)
        db.groups.delete_all()
        db.groups.create_by_names(groups)
        db.tasks.delete_all()
        db.tasks.create_by_ids(tasks)
        db.variants.delete_all()
        db.variants.create_by_ids(range(0, 39 + 1))
        print(f'Successfully seeded db {connection} using core {core}!')


class AnalyzeCmd:
    def __init__(self):
        self.command = "--analyze"
        self.help = "evaluates analytics for all accepted programs"

    def run(self, dir: str):
        print('Analyzing accepted programs...')
        pass
