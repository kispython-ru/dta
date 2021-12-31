from functools import wraps
from flask.templating import render_template
from flask_jwt_extended.utils import get_jwt_identity
from flask_jwt_extended.view_decorators import verify_jwt_in_request
from flask import redirect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from flask import current_app as app
import os
import json

Base = declarative_base()


def authorize(redirect_url="/login", redirect_if_authorized=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=True)
                logged_in = get_jwt_identity()
                if not redirect_if_authorized and not logged_in or redirect_if_authorized and logged_in:
                    return redirect(redirect_url)
                return fn(*args, **kwargs)
            except Exception as e:
                app.logger.error(e)
                return render_template(
                    "error.jinja",
                    error_code=500,
                    error_message="An error has occured.",
                    error_redirect="/logout")
        return decorator
    return wrapper


def handle_errors(
        error_message="Error has occured.",
        error_code=500,
        error_redirect="/"):
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
                    error_redirect=error_redirect)
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
    connection_string = app.config['CONNECTION_STRING']
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory()


def load_config_files(directory_name: str):
    merged = {}
    for file in os.listdir(directory_name):
        if file.endswith(".json"):
            print(f"Merging {file}")
            with open(file, mode='r') as configuration:
                content = configuration.read()
                json_content = json.loads(content)
                merged = {**merged, **json_content}
    print(json.dumps(merged, indent=2))
    return merged
