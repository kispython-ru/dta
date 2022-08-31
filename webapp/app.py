import logging
import os

from flask_jwt_extended import JWTManager

from flask import Flask

import webapp.views.api as api
import webapp.views.student as student
import webapp.views.teacher as teacher
import webapp.worker as worker
from alembic import command
from alembic.config import Config
from webapp.managers import AppConfigManager
from webapp.repositories import AppDatabase
from webapp.utils import load_config_files


def migrate_database(connection_string: str):
    base = os.path.dirname(os.path.abspath(__file__))
    ini = os.path.join(base, "alembic.ini")
    script = os.path.join(base, "alembic")
    config = Config(ini)
    config.set_main_option("sqlalchemy.url", connection_string)
    if script is not None:
        config.set_main_option("script_location", script)
    command.upgrade(config, "head")


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
    app.config["JWT_SECRET_KEY"] = config["SECRET_KEY"]
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JSON_AS_ASCII"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
    app.config.update(config)
    app.register_blueprint(student.blueprint)
    app.register_blueprint(teacher.blueprint)
    app.register_blueprint(api.blueprint)
    app.register_blueprint(worker.blueprint)
    JWTManager(app)
    logging.basicConfig(level=logging.DEBUG)
    migrate_database(config["CONNECTION_STRING"])
    seed_database(app)
    return app


def create_app() -> Flask:
    path = os.environ.get("CONFIG_PATH")
    configuration_directory = path if path is not None else os.getcwd()
    return configure_app(configuration_directory)
