from werkzeug.exceptions import HTTPException

from flask import Blueprint
from flask import current_app as app
from flask import render_template, request

from webapp.forms import MessageForm
from webapp.managers import AppConfigManager, GroupManager, StatusManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip


blueprint = Blueprint("student", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)
statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
groups = GroupManager(config, db.groups, db.seeds)


@blueprint.route("/", methods=["GET"])
def dashboard():
    groupings = groups.get_groupings()
    exam = config.config.final_tasks is not None
    return render_template("student/dashboard.jinja", groupings=groupings, exam=exam)


@blueprint.route("/group/<group_id>", methods=["GET"])
def group(group_id: int):
    group = statuses.get_group_statuses(group_id)
    seed = db.seeds.get_final_seed(group_id)
    blocked = config.config.final_tasks and seed is None
    return render_template("student/group.jinja", group=group, blocked=blocked)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
def task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    highlight = config.config.highlight_syntax
    return render_template(
        "student/task.jinja",
        status=status,
        form=MessageForm(),
        highlight=highlight,
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
def submit_task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    form = MessageForm()
    valid = form.validate_on_submit() and not status.checked
    available = status.external.active and not config.config.readonly
    if valid and available:
        code = form.code.data
        ip = get_real_ip(request)
        db.messages.submit_task(tid, vid, gid, code, ip)
        db.statuses.submit_task(tid, vid, gid, code, ip)
        return render_template("student/success.jinja", status=status)
    highlight = config.config.highlight_syntax
    return render_template(
        "student/task.jinja",
        status=status,
        form=form,
        highlight=highlight,
    )


@blueprint.errorhandler(Exception)
def handle_views_errors(error):
    error_code = error.code if isinstance(error, HTTPException) else 500
    print(get_exception_info())
    return render_template(
        "error.jinja",
        error_code=error_code,
        error_message="Error has occured.",
        error_redirect="/",
    )
