import logging
import os
from datetime import timedelta

from flask_jwt_extended import JWTManager

from flask import Flask

import webapp.mailbox as mailbox
import webapp.views.api as api
import webapp.views.student as student
import webapp.views.teacher as teacher
import webapp.worker as worker
from webapp.commands import AnalyzeCmd, CmdManager, SeedCmd, migrate
from webapp.dto import AppConfig
from webapp.utils import load_config_files


def configure_app(directory: str) -> Flask:
    config = load_config_files(directory)
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config["JWT_SECRET_KEY"] = config["SECRET_KEY"]
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=6)
    app.config["JWT_VERIFY_SUB"] = False
    app.config["JSON_AS_ASCII"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
    app.config.update(config)
    app.register_blueprint(student.blueprint)
    app.register_blueprint(teacher.blueprint)
    app.register_blueprint(api.blueprint)
    JWTManager(app)
    logging.basicConfig(level=logging.DEBUG)
    migrate(config["CONNECTION_STRING"])
    return app


def configure_background_services(app: Flask) -> Flask:
    config = AppConfig(app.config)
    app.config["WORKER_PID"] = worker.start_background_worker(config)
    app.config["MAILBOX_PID"] = mailbox.start_background_worker(config)
    return app


def config() -> str:
    path = os.environ.get("CONFIG_PATH")
    directory = path if path else os.path.join(os.getcwd(), 'webapp')
    return directory


def create_app() -> Flask:
    return configure_background_services(configure_app(config()))


if __name__ == "__main__":
    cmd = CmdManager(config(), [SeedCmd, AnalyzeCmd])
    cmd.run()
