from werkzeug.exceptions import HTTPException

from flask import Blueprint
from flask import current_app as app
from flask import jsonify, request

from webapp.forms import CodeLength
from webapp.managers import find_task_status
from webapp.models import TaskStatusEnum
from webapp.repositories import AppDatabase
from webapp.utils import get_real_ip


blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
db = AppDatabase(lambda: app.config["CONNECTION_STRING"])


@blueprint.route("/group/prefixes", methods=["GET"])
def group_prefixes():
    groupings = db.groups.get_groupings()
    keys = list(groupings.keys())
    return jsonify(dict(prefixes=keys))


@blueprint.route("/group/<prefix>", methods=["GET"])
def group(prefix: str):
    groups = db.groups.get_by_prefix(prefix)
    dtos = [dict(id=group.id, title=group.title) for group in groups]
    return jsonify(dtos)


@blueprint.route("/variant/list", methods=["GET"])
def variant_list():
    variants = db.variants.get_all()
    dtos = [variant.id for variant in variants]
    return jsonify(dtos)


@blueprint.route("/group/<gid>/variant/<vid>/task/list", methods=["GET"])
def task_list(gid: int, vid: int):
    variant = db.variants.get_by_id(vid)
    tasks = db.tasks.get_all()
    group = db.groups.get_by_id(gid)
    statuses = db.statuses.get_by_group(group.id)
    base_url = app.config["TASK_BASE_URL"]
    dtos = []
    for task in tasks:
        vid = variant.id + 1
        source = f"{base_url}/{task.id}/{group.title}.html#вариант-{vid}"
        status = find_task_status(statuses, group.id, variant.id, task.id)
        dtos.append(dict(
            id=task.id,
            source=source,
            status=status.value,
            status_name=status.name,
        ))
    return jsonify(dtos)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
def task(gid: int, vid: int, tid: int):
    variant = db.variants.get_by_id(vid)
    group = db.groups.get_by_id(gid)
    task = db.tasks.get_by_id(tid)
    ts = db.statuses.get_task_status(task.id, variant.id, group.id)
    error_message = ts.output if ts is not None else ""
    status = ts.status if ts is not None else TaskStatusEnum.NotSubmitted
    url = app.config["TASK_BASE_URL"]
    source = f"{url}/{task.id}/{group.title}.html#вариант-{variant.id + 1}"
    return jsonify(dict(
        id=task.id,
        source=source,
        status=status.value,
        status_name=status.name,
        error_message=error_message,
    ))


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
def submit_task(gid: int, vid: int, tid: int):
    if app.config["API_TOKEN"] != request.headers.get("token"):
        raise ValueError("Access is denied.")
    if not CodeLength.min < len(request.json["code"]) < CodeLength.max:
        return ValueError("Bad request.")

    variant = db.variants.get_by_id(vid)
    group = db.groups.get_by_id(gid)
    task = db.tasks.get_by_id(tid)
    ip = get_real_ip(request)
    code = request.json["code"]

    db.messages.submit_task(task.id, variant.id, group.id, code, ip)
    ts = db.statuses.submit_task(task.id, variant.id, group.id, code)
    error_message = ts.output if ts is not None else ""
    status = ts.status if ts is not None else TaskStatusEnum.NotSubmitted
    url = app.config["TASK_BASE_URL"]
    source = f"{url}/{task.id}/{group.title}.html#вариант-{variant.id + 1}"
    return jsonify(dict(
        id=task.id,
        source=source,
        status=status.value,
        status_name=status.name,
        error_message=error_message,
    ))


@blueprint.errorhandler(Exception)
def handle_api_errors(error):
    error_code = error.code if isinstance(error, HTTPException) else 500
    return jsonify(dict(error=error_code))
