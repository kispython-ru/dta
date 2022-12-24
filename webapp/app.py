import logging
import mailbox
import os

from flask_jwt_extended import JWTManager

from flask import Flask

import webapp.mailbox as mailbox
import webapp.views.api as api
import webapp.views.student as student
import webapp.views.teacher as teacher
import webapp.worker as worker
from alembic import command
from alembic.config import Config
from webapp.commands import AnalyzeCmd, CmdManager, SeedCmd
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


def configure(directory: str) -> Flask:
    config = load_config_files(directory)
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config["JWT_SECRET_KEY"] = config["SECRET_KEY"]
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JSON_AS_ASCII"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
    app.config.update(config)
    app.register_blueprint(student.blueprint)
    app.register_blueprint(teacher.blueprint)
    app.register_blueprint(api.blueprint)
    app.register_blueprint(worker.blueprint)
    app.register_blueprint(mailbox.blueprint)
    JWTManager(app)
    logging.basicConfig(level=logging.DEBUG)
    migrate(config["CONNECTION_STRING"])
    return app


def config_path() -> str:
    path = os.environ.get("CONFIG_PATH")
    directory = path if path else os.path.join(os.getcwd(), 'webapp')
    return directory


def create_app() -> Flask:
    dir = config_path()
    return configure(dir)


if __name__ == "__main__":
    dir = config_path()
    cmd = CmdManager(dir, [SeedCmd, AnalyzeCmd])
    cmd.run()
