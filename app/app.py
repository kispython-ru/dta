import logging
import os
from flask import Flask
from app.utils import create_session, load_config_files
import alembic.config
import app.views as views
from app.managers import AppDbContext
import app.worker as worker


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    config = load_config_files(os.getcwd())
    app.config.update(config)
    app.register_blueprint(views.blueprint)
    app.register_blueprint(worker.blueprint)
    logging.basicConfig(level=logging.DEBUG)
    connection_string = config['CONNECTION_STRING']
    alembic.config.main(
        prog='alembic',
        argv=[
            '--raiseerr',
            '-x',
            f'connection_string={connection_string}',
            'upgrade',
            'head'])
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
    db.tasks.create_by_names(["1.1"])
    db.variants.delete_all()
    db.variants.create_many(40)
