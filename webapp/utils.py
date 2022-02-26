import json
import os
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from flask import current_app as app
from flask.templating import render_template


Base = declarative_base()


def handle_errors(
        error_message="Error has occured.",
        error_code=500,
        error_redirect="/",
):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as error:
                app.logger.error(error)
                return render_template(
                    "error.jinja",
                    error_code=error_code,
                    error_message=error_message,
                    error_redirect=error_redirect,
                )
        return decorator
    return wrapper


def use_session():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            session = create_session()
            try:
                return fn(session, *args, **kwargs)
            except IntegrityError:
                session.rollback()
                raise
            finally:
                session.close()
        return decorator
    return wrapper


def create_session() -> Session:
    connection_string = app.config["CONNECTION_STRING"]
    return create_session_manually(connection_string)


def create_session_manually(connection_string: str) -> Session:
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory()


def load_config_files(directory_name: str):
    merged = {}
    for config_file in os.listdir(directory_name):
        if config_file.endswith(".json"):
            path = os.path.join(directory_name, config_file)
            print(f"Merging {path}")
            with open(path, mode="r") as configuration:
                content = configuration.read()
                json_content = json.loads(content)
                merged = {**merged, **json_content}
    print(json.dumps(merged, indent=2))
    return merged
