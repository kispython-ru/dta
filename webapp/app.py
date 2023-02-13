import logging
import mailbox
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
from webapp.lks import lks_oauth_helper
from webapp.utils import load_config_files


def configure_lks_oauth(app: Flask, config: dict) -> None:
    """Create LKS OAuth client if it is enabled"""
    if not all(
        key in config
        for key in [
            "ENABLE_LKS_OAUTH",
            "LKS_OAUTH_CLIENT_ID",
            "LKS_OAUTH_CLIENT_SECRET",
            "LKS_API_BASE_URL",
        ]
    ):
        return

    if not config["ENABLE_LKS_OAUTH"]:
        return

    if not config["LKS_OAUTH_CLIENT_ID"] or not config["LKS_OAUTH_CLIENT_SECRET"]:
        raise ValueError("LKS OAuth is enabled, but client id or secret is not set")

    lks_oauth_helper.register(
        app,
        config["LKS_OAUTH_CLIENT_ID"],
        config["LKS_OAUTH_CLIENT_SECRET"],
        config["LKS_API_BASE_URL"],
    )


def configure_app(directory: str) -> Flask:
    config = load_config_files(directory)
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config["JWT_SECRET_KEY"] = config["SECRET_KEY"]
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=6)
    app.config["JSON_AS_ASCII"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
    app.config.update(config)
    configure_lks_oauth(app, config)
    app.register_blueprint(student.blueprint)
    app.register_blueprint(teacher.blueprint)
    app.register_blueprint(api.blueprint)
    app.register_blueprint(worker.blueprint)
    app.register_blueprint(mailbox.blueprint)
    JWTManager(app)
    logging.basicConfig(level=logging.DEBUG)
    migrate(config["CONNECTION_STRING"])

    return app


def config() -> str:
    path = os.environ.get("CONFIG_PATH")
    directory = path if path else os.path.join(os.getcwd(), "webapp")
    return directory


def create_app() -> Flask:
    return configure_app(config())


if __name__ == "__main__":
    cmd = CmdManager(config(), [SeedCmd, AnalyzeCmd])
    cmd.run()
