from flask import Blueprint
from flask import current_app as app
from flask import jsonify, request

from webapp.forms import CodeLength
from webapp.managers import AppConfigManager, GroupManager, StatusManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip


blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
groups = GroupManager(config, db.groups, db.seeds)


@blueprint.route("/group/prefixes", methods=["GET"])
def group_prefixes():
    groupings = groups.get_groupings()
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
    variant = statuses.get_variant_statuses(gid, vid)
    response = [dict(
        id=status.task,
        source=status.formulation_url,
        status=status.status.value,
        status_name=status.name,
    ) for status in variant.statuses]
    return jsonify(response)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
def task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    return jsonify(dict(
        id=status.task,
        source=status.formulation_url,
        status=status.status.value,
        status_name=status.name,
        error_message=status.error_message,
    ))


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
def submit_task(gid: int, vid: int, tid: int):
    token = request.headers.get("token")
    if config.config.api_token != token:
        raise ValueError("Access is denied.")
    code = request.json["code"]
    if not CodeLength.min < len(code) < CodeLength.max:
        raise ValueError("Code length is invalid.")
    status = statuses.get_task_status(gid, vid, tid)
    if status.disabled:
        raise ValueError("Submissions are disallowed.")
    ip = get_real_ip(request)
    db.messages.submit_task(tid, vid, gid, code, ip, None)
    db.statuses.submit_task(tid, vid, gid, code, ip)
    status = statuses.get_task_status(gid, vid, tid)
    return jsonify(dict(
        id=status.task,
        source=status.formulation_url,
        status=status.status.value,
        status_name=status.name,
        error_message=status.error_message,
    ))


@blueprint.errorhandler(Exception)
def handle_view_errors(e):
    print(get_exception_info())
    return jsonify(dict(error=500))
