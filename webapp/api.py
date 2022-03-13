from flask import Blueprint, jsonify

from webapp.managers import find_task_status
from webapp.repositories import AppDbContext
from webapp.utils import handle_api_errors, use_db


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
    dtos = []
    for task in tasks:
        variant_id = variant.id + 1
        source = f"http://sovietov.com/kispython/{task.id}/{group.title}.html#вариант-{variant_id}"
        status = find_task_status(statuses, group.id, variant.id, task.id)
        dtos.append({
            "id": task.id,
            "source": source,
            "status": status.value,
            "status_name": status.name,
        })
    return jsonify(dtos)
