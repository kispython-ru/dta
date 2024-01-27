import json
import os
import sys
import traceback
from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, unset_jwt_cookies, verify_jwt_in_request
from jwt import PyJWTError

from flask import Request, redirect

from webapp.managers import AppConfigManager
from webapp.repositories import StudentRepository, TeacherRepository


def student_jwt_reset(config: AppConfigManager, path: str):
    def wrapper(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            if not config.config.registration:
                return redirect('/')
            if verify_jwt_in_request(True):
                response = redirect(path)
                unset_jwt_cookies(response)
                return response
            return function(*args, **kwargs)
        return decorator
    return wrapper


def student_jwt_optional(students: StudentRepository):
    def wrapper(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity is None:
                return function(None, *args, **kwargs)
            claims = get_jwt()
            if "teacher" in claims:
                return function(None, *args, **kwargs)
            student = students.get_by_id(identity)
            return function(student, *args, **kwargs)
        return decorator
    return wrapper


def teacher_jwt_required(teachers: TeacherRepository):
    def wrapper(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if "teacher" in claims:
                identity = get_jwt_identity()
                teacher = teachers.get_by_id(identity)
                if teacher:
                    return function(teacher, *args, **kwargs)
                raise PyJWTError()
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
            with open(path, mode="r") as configuration:
                content = configuration.read()
                json_content = json.loads(content)
                merged = {**merged, **json_content}
    print(json.dumps(merged, indent=2))
    return merged
