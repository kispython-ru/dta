import functools
import json
import os
import sys
import traceback
from typing import Callable

from flask import Request, render_template


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


def require_token(get_token: Callable[[], str]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = get_token()
            if 'token' not in kwargs or token != kwargs['token']:
                return render_template(
                    "error.jinja",
                    error_code=401,
                    error_message="Unauthorized",
                    error_redirect="/",
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
