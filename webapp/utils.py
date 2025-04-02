import json
import os
import sys
import traceback
from datetime import datetime
from functools import wraps
from typing import Callable

from flask_jwt_extended import get_jwt_identity, unset_jwt_cookies, verify_jwt_in_request
from jwt import PyJWTError

from flask import Request, redirect

from webapp.managers import AppConfigManager
from webapp.models import Student
from webapp.repositories import StudentRepository


def logout(config: AppConfigManager, path: str, auth_redirect=True):
    def wrapper(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            if not config.config.registration and auth_redirect:
                return redirect("/")
            if verify_jwt_in_request(True):
                response = redirect(path)
                unset_jwt_cookies(response)
                return response
            return function(*args, **kwargs)
        return decorator
    return wrapper


def authorize(students: StudentRepository, check: Callable[[Student], bool] | None = None):
    def wrapper(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            verify_jwt_in_request(optional=not check)
            identity = get_jwt_identity()
            if identity is None:
                return function(None, *args, **kwargs)
            student = students.get_by_id(identity)
            if not check or check(student):
                return function(student, *args, **kwargs)
            raise PyJWTError()
        return decorator
    return wrapper


def get_real_ip(request: Request) -> str:
    ip_forward_headers = request.headers.getlist("X-Forwarded-For")
    if ip_forward_headers:
        return ip_forward_headers[0]
    return request.remote_addr


def get_exception_info() -> str:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(
        exc_type, exc_value, exc_traceback)
    log = "".join("!! " + line for line in lines)
    return log


def load_config_files(directory_name: str):
    merged = {}
    for config_file in sorted(os.listdir(directory_name)):
        if config_file.endswith(".json"):
            path = os.path.join(directory_name, config_file)
            print(f"Merging {path}")
            with open(path, mode="r", encoding='utf-8') as configuration:
                content = configuration.read()
                json_content = json.loads(content)
                merged = {**merged, **json_content}
    print(json.dumps(merged, indent=2))
    return merged


def get_time(string_time):
    return datetime.strptime(string_time, "%H:%M").time()


def get_greeting_msg():
    current_time = datetime.now().time()
    if get_time("06:00") <= current_time < get_time("12:00"):
        return "Доброе утро"
    if get_time("12:00") <= current_time < get_time("18:00"):
        return "Добрый день"
    if get_time("18:00") <= current_time < get_time("22:00"):
        return "Добрый вечер"
    return "Доброй ночи"
