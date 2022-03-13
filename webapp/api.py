from flask import Blueprint, jsonify

from webapp.repositories import AppDbContext
from webapp.utils import handle_errors, use_db


blueprint = Blueprint("api", __name__)


@blueprint.route("/api/group/prefixes", methods=["GET"])
@handle_errors()
@use_db()
def prefixes(db: AppDbContext):
    groupings = db.groups.get_groupings()
    keys = list(groupings.keys())
    return jsonify({"prefixes": keys})


@blueprint.route("/api/group/<prefix>", methods=["GET"])
@handle_errors()
@use_db()
def group(db: AppDbContext, prefix: str):
    groups = db.groups.get_by_prefix(prefix)
    dtos = [{ "id": group.id, "title": group.title } for group in groups]
    return jsonify(dtos)
