from flask import Blueprint, jsonify

from webapp.managers import AppDbContext
from webapp.utils import handle_errors, use_db


blueprint = Blueprint("api", __name__)


@blueprint.route("/api/group-prefixes", methods=["GET"])
@handle_errors()
@use_db()
def dashboard(db: AppDbContext):
    groupings = db.groups.get_groupings()
    keys = list(groupings.keys())
    return jsonify(keys)
