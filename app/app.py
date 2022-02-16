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
            seed_app(app.config['CORE_PATH'])
    return app


def seed_app(core_path: str):
    groups, tasks = worker.load_tests(core_path)
    session = create_session()
    db = AppDbContext(session)
    db.groups.delete_all()
    db.groups.create_by_names(groups)
    db.tasks.delete_all()
    db.tasks.create_by_names(tasks)
    db.variants.delete_all()
    db.variants.create_by_ids(range(0, 39))
