from flask import Blueprint
from flask import current_app as app
from flask import jsonify, request

from webapp.forms import CodeLength, MessageFormParameters
from webapp.managers import find_task_status
from webapp.models import TaskStatus, TaskStatusEnum
from webapp.repositories import AppDbContext
from webapp.utils import get_real_ip, handle_api_errors, use_db


blueprint = Blueprint("api", __name__, url_prefix="/api/v1")


@blueprint.route("/group/prefixes", methods=["GET"])
@handle_api_errors()
@use_db()
def group_prefixes(db: AppDbContext):
    groupings = db.groups.get_groupings()
    keys = list(groupings.keys())
    return jsonify({
        "prefixes": keys,
    })


@blueprint.route("/group/<prefix>", methods=["GET"])
@handle_api_errors()
@use_db()
def group(db: AppDbContext, prefix: str):
    groups = db.groups.get_by_prefix(prefix)
    dtos = []
    for group in groups:
        dtos.append({
            "id": group.id,
            "title": group.title,
        })
    return jsonify(dtos)


@blueprint.route("/variant/list", methods=["GET"])
@handle_api_errors()
@use_db()
def variant_list(db: AppDbContext):
    variants = db.variants.get_all()
    dtos = [variant.id for variant in variants]
    return jsonify(dtos)


@blueprint.route("/group/<gid>/variant/<vid>/task/list", methods=["GET"])
@handle_api_errors()
@use_db()
def task_list(db: AppDbContext, gid: int, vid: int):
    variant = db.variants.get_by_id(vid)
    tasks = db.tasks.get_all()
    group = db.groups.get_by_id(gid)
    statuses = db.statuses.get_by_group(group.id)
    path = "http://sovietov.com/kispython"
    dtos = []
    for task in tasks:
        variant_id = variant.id + 1
        source = f"{path}/{task.id}/{group.title}.html#вариант-{variant_id}"
        status = find_task_status(statuses, group.id, variant.id, task.id)
        dtos.append({
            "id": task.id,
            "source": source,
            "status": status.value,
            "status_name": status.name,
        })
    return jsonify(dtos)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
@handle_api_errors()
@use_db()
def task(db: AppDbContext, gid: int, vid: int, tid: int):
    variant = db.variants.get_by_id(vid)
    group = db.groups.get_by_id(gid)
    task = db.tasks.get_by_id(tid)
    ts = db.statuses.get_task_status(task.id, variant.id, group.id)
    error_message = ts.output if ts is not None else ""
    status = ts.status if ts is not None else TaskStatusEnum.NotSubmitted
    path = "http://sovietov.com/kispython"
    return jsonify({
        "id": task.id,
        "source": f"{path}/{task.id}/{group.title}.html#вариант-{variant.id}",
        "status": status.value,
        "status_name": status.name,
        "error_message": error_message,
    })


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
@handle_api_errors()
@use_db()
def submit_task(db: AppDbContext, gid: int, vid: int, tid: int):
    if app.config["API_TOKEN"] != request.authorization.get("Basic"):
        raise ValueError("Access is denied.")

    json = request.get_json()
    code = json["code"]
    if not CodeLength.min < len(code) < CodeLength.max:
        return ValueError("Bad request.")

    variant = db.variants.get_by_id(vid)
    group = db.groups.get_by_id(gid)
    task = db.tasks.get_by_id(tid)
    ip = get_real_ip(request)

    db.messages.submit_task(task.id, variant.id, group.id, code, ip)
    ts = db.statuses.submit_task(task.id, variant.id, group.id, code)
    error_message = ts.output if ts is not None else ""
    status = ts.status if ts is not None else TaskStatusEnum.NotSubmitted
    path = "http://sovietov.com/kispython"
    return jsonify({
        "id": task.id,
        "source": f"{path}/{task.id}/{group.title}.html#вариант-{variant.id}",
        "status": status.value,
        "status_name": status.name,
        "error_message": error_message,
    })
