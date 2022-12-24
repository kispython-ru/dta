from argparse import ArgumentParser
from typing import Any, Callable

import webapp.worker as worker
from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import load_config_files
import os


class CmdManager:
    def __init__(self, commands: list[Callable[[str], Any]]):
        self.runners: dict[str, Any] = dict()
        self.parser = ArgumentParser()
        self.parser.add_argument("--cwd", help="working directory", required=True)
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
        args = vars(self.parser.parse_args())
        directory = os.path.abspath(args.pop('cwd'))
        os.chdir(directory)
        executed = False
        for key, enabled in args.items():
            if not enabled:
                continue
            print(f'Running {key} cmd...')
            runner = self.runners[key]
            runner.run(directory)
            executed = True
        return executed


class SeedCmd:
    def __init__(self):
        self.command = "--seed"
        self.help = "seeds the database using core"

    def run(self, dir: str):
        print(f'Seeding the database using config from {dir}')
        manager = AppConfigManager(lambda: load_config_files(dir))
        groups, tasks = worker.load_tests(manager.config.core_path)
        db = AppDatabase(lambda: manager.config.connection_string)
        db.groups.delete_all()
        db.groups.create_by_names(groups)
        db.tasks.delete_all()
        db.tasks.create_by_ids(tasks)
        db.variants.delete_all()
        db.variants.create_by_ids(range(0, 39 + 1))


class UpdateAnalyticsCmd:
    def __init__(self):
        self.command = "--update-analytics"
        self.help = "evaluates analytics for all accepted programs"

    def run(self, dir: str):
        print('Updating analytics responses...')
        pass
