import logging
import os
from typing import Union

from flask import Flask

import webapp.api as api
import webapp.views as views
import webapp.worker as worker
from alembic import command
from alembic.config import Config
from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import load_config_files


def migrate_database(connection_string: str, alembic_path: str):
    alembic_ini_path = os.path.join(alembic_path, "alembic.ini")
    alembic_script_path = os.path.join(alembic_path, "alembic")
    alembic_config = Config(alembic_ini_path)
    alembic_config.set_main_option("sqlalchemy.url", connection_string)
    if alembic_script_path is not None:
        alembic_config.set_main_option("script_location", alembic_script_path)
    command.upgrade(alembic_config, "head")


def seed_database(app: Flask):
    print("Checking if we need to seed the database...")
    if os.environ.get("SEED") is None:
        print("We don't need to seed the database.")
        return
    print("Seeding the database now...")
    with app.app_context():
        config = AppConfigManager(lambda: app.config)
        groups, tasks = worker.load_tests(config.config.core_path)
        db = AppDatabase(lambda: config.config.connection_string)
        db.groups.delete_all()
        db.groups.create_by_names(groups)
        db.tasks.delete_all()
        db.tasks.create_by_ids(tasks)
        db.variants.delete_all()
        db.variants.create_by_ids(range(0, 39 + 1))
    print("Successfully seeded the dabatase!")


def configure_app(config_path: str) -> Flask:
    config = load_config_files(config_path)
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.update(config)
    app.register_blueprint(views.blueprint)
    app.register_blueprint(worker.blueprint)
    app.register_blueprint(api.blueprint)
    logging.basicConfig(level=logging.DEBUG)
    migrate_database(config["CONNECTION_STRING"], config["ALEMBIC_PATH"])
    seed_database(app)
    return app


def create_app() -> Flask:
    path = os.environ.get("CONFIG_PATH")
    configuration_directory = path if path is not None else os.getcwd()
    return configure_app(configuration_directory)
