from argparse import ArgumentParser
from typing import Callable

import webapp.worker as worker
from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import load_config_files


class Cmd:
    def __init__(self, dir: str, command: str, help: str):
        self.dir = dir
        self.command = command
        self.help = help

    def run(self):
        pass


class CmdManager:
    def __init__(self, dir: str, commands: list[Callable[[str], Cmd]]):
        self.parser = ArgumentParser()
        self.runners: dict[str, Cmd] = dict()
        for command in commands:
            runner = command(dir)
            key = runner.command.strip('-')
            self.runners[key] = runner
            self.parser.add_argument(
                runner.command,
                help=runner.help,
                required=False,
                action='store_true'
            )

    def run(self) -> bool:
        executed = False
        args = self.parser.parse_args()
        for key, enabled in vars(args).items():
            if not enabled:
                continue
            print(f'Running {key} cmd...')
            runner = self.runners[key]
            runner.run()
            executed = True
        return executed


class SeedCmd(Cmd):
    def __init__(self, dir: str):
        super().__init__(dir, "--seed", "Seeds the database using data from core.")

    def run(self):
        print(f'Seeding the database using config from {self.dir}')
        manager = AppConfigManager(lambda: load_config_files(self.dir))
        groups, tasks = worker.load_tests(manager.config.core_path)
        db = AppDatabase(lambda: manager.config.connection_string)
        db.groups.delete_all()
        db.groups.create_by_names(groups)
        db.tasks.delete_all()
        db.tasks.create_by_ids(tasks)
        db.variants.delete_all()
        db.variants.create_by_ids(range(0, 39 + 1))


class UpdateAnalyticsCmd(Cmd):
    def __init__(self, dir: str):
        super().__init__(dir, "--update-analytics", "Evaluates analytics for all accepted programs.")

    def run(self):
        print('Updating analytics responses...')
        pass
