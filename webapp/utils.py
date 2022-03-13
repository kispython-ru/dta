import json
import os
from functools import wraps

from sqlalchemy.exc import IntegrityError

from flask import current_app as app
from flask.templating import render_template

from webapp.managers import AppDbContext
from webapp.models import create_session


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


def use_db():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            session = create_session()
            try:
                db = AppDbContext(session)
                return fn(db, *args, **kwargs)
            except IntegrityError:
                session.rollback()
                raise
            finally:
                session.close()
        return decorator
    return wrapper


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
