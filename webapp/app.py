import logging
import os
from flask import Flask
from webapp.utils import create_session, load_config_files
import alembic.config
import webapp.views as views
from webapp.managers import AppDbContext
import webapp.worker as worker


def migrate_database(connection_string: str):
    alembic.config.main(
        prog='alembic',
        argv=[
            '--raiseerr',
            '-x',
            f'connection_string={connection_string}',
            'upgrade',
            'head'])


def seed_database(app: Flask):
    if os.environ.get('SEED') != 1:
        return
    with app.app_context():
        core_path = app.config['CORE_PATH']
        groups, tasks = worker.load_tests(core_path)
        session = create_session()
        db = AppDbContext(session)
        db.groups.delete_all()
        db.groups.create_by_names(groups)
        db.tasks.delete_all()
        db.tasks.create_by_names(tasks)
        db.variants.delete_all()
        db.variants.create_by_ids(range(0, 39))


def read_configuration():
    config_path = os.environ.get('CONFIG_PATH')
    configuration_directory = config_path if config_path is not None else os.getcwd()
    return load_config_files(configuration_directory)


def create_app():
    config = read_configuration()
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.update(config)
    app.register_blueprint(views.blueprint)
    app.register_blueprint(worker.blueprint)
    logging.basicConfig(level=logging.DEBUG)
    migrate_database(config['CONNECTION_STRING'])
    seed_database(app)
    return app
