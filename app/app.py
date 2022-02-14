import logging
import os
import sys
from flask import Flask
from app.utils import create_session, load_config_files, use_session
import alembic.config
import app.views as views
from sqlalchemy.orm import Session
from app.managers import AppDbContext


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.update(load_config_files(os.getcwd()))
    app.register_blueprint(views.blueprint)
    logging.basicConfig(level=logging.DEBUG)
    alembic.config.main(prog='alembic', argv=['--raiseerr', 'upgrade', 'head'])
    if os.environ.get('SEED'):
        with app.app_context():
            seed_app()
    return app


def seed_app():
    ivbo = [f'ИВБО-{i:02d}-20' for i in range(1, 9)] + ['ИВБО-13-20']
    ikbo = [f'ИКБО-{i:02d}-20' for i in range(1, 28)] + ['ИКБО-30-20']
    inbo = [
        f'ИНБО-{i:02d}-20' for i in range(1, 12)] + ['ИНБО-13-15', 'ИНБО-15-20']
    imbo = [f'ИМБО-{i:02d}-20' for i in range(1, 3)]
    groups = ivbo + ikbo + inbo + imbo
    session = create_session()
    db = AppDbContext(session)
    db.groups.delete_all()
    db.groups.create_by_names(groups)
    db.tasks.delete_all()
    db.tasks.create_by_names(["Реализовать функцию"])
    db.variants.delete_all()
    db.variants.create_many(40)
