import logging
import os
from flask import Flask
from flask_jwt_extended import JWTManager
from app.utils import load_config_files
import alembic.config
import app.views as views


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.update(load_config_files(os.getcwd()))
    app.register_blueprint(views.blueprint)
    jwt = JWTManager(app)
    logging.basicConfig(level=logging.DEBUG)
    alembic.config.main(prog='alembic', argv=['--raiseerr', 'upgrade', 'head'])
    return app
