from typing import Union

from werkzeug.exceptions import HTTPException

from flask import Blueprint
from flask import current_app as app
from flask import make_response, redirect, render_template, request, url_for

from webapp.forms import MessageForm
from webapp.managers import (
    AppConfigManager,
    ExportManager,
    GroupManager,
    StatusManager
)
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip, require_token


blueprint = Blueprint("views", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)
groups = GroupManager(
    config=config,
    groups=db.groups,
    seeds=db.seeds,
)

statuses = StatusManager(
    tasks=db.tasks,
    groups=db.groups,
    variants=db.variants,
    statuses=db.statuses,
    config=config,
    seeds=db.seeds
)

exports = ExportManager(
    statuses=statuses,
    groups=db.groups,
    messages=db.messages,
    variants=db.variants,
    tasks=db.tasks
)


@blueprint.route("/", methods=["GET"])
def dashboard():
    groupings = groups.get_groupings()
    exam = config.config.final_tasks is not None
    return render_template("dashboard.jinja", groupings=groupings, exam=exam)


@blueprint.route("/group/<group_id>", methods=["GET"])
def group(group_id: int):
    group = statuses.get_group_statuses(group_id)
    seed = db.seeds.get_final_seed(group_id)
    blocked = config.config.final_tasks and seed is None
    return render_template("group.jinja", group=group, blocked=blocked)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
def task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    highlight = config.config.highlight_syntax
    return render_template(
        "task.jinja",
        status=status,
        form=MessageForm(),
        highlight=highlight,
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
def submit_task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    form = MessageForm()
    valid = form.validate_on_submit()
    if valid and not status.checked and status.external.active:
        code = form.code.data
        db.messages.submit_task(tid, vid, gid, code, get_real_ip(request))
        db.statuses.submit_task(tid, vid, gid, code)
        return render_template("success.jinja", status=status)
    highlight = config.config.highlight_syntax
    return render_template(
        "task.jinja",
        status=status,
        form=form,
        highlight=highlight,
    )


@blueprint.route("/csv/<s>/<token>/<count>", methods=["GET"])
@blueprint.route("/csv/<s>/<token>", methods=["GET"], defaults={"count": None})
def export(s: str, token: str, count: Union[int, None]):
    if config.config.csv_token != token:
        raise ValueError("Access is denied.")
    value = exports.export_messages(count, s)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/exams/<token>", methods=["GET"])
@require_token(lambda: config.config.final_token)
def exams(token: str):
    groups = db.groups.get_all()
    return render_template("exams.jinja", groups=groups, token=token)


@blueprint.route("/exams/<token>", methods=["POST"])
@require_token(lambda: config.config.final_token)
def enter_exam_group(token: str):
    group_id = request.form.get('group')
    return redirect(url_for("views.pre_exam", group_id=group_id, token=token))


@blueprint.route("/exams/<token>/<group_id>", methods=["GET"])
@require_token(lambda: config.config.final_token)
def pre_exam(group_id: int, token: str):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template("exam.jinja", group=group, seed=seed, token=token)


@blueprint.route("/exams/<token>/<group_id>", methods=["POST"])
@require_token(lambda: config.config.final_token)
def exam(group_id: int, token: str):
    seed = db.seeds.get_final_seed(group_id)
    if seed is None and config.config.final_tasks:
        db.seeds.begin_final_test(group_id)
    elif seed.active:
        db.seeds.end_final_test(group_id)
    else:
        db.seeds.continue_final_test(group_id)
    seed = db.seeds.get_final_seed(group_id)
    group = db.groups.get_by_id(group_id)
    return render_template("exam.jinja", group=group, seed=seed, token=token)


@blueprint.route("/exams/<token>/<gid>/score_csv", methods=["POST"])
@require_token(lambda: config.config.final_token)
def score_csv(gid: int, token: str):
    delimiter = request.form.get('delimiter')
    value = exports.export_exam_results(gid, delimiter)
    output = make_response(value)
    output.headers["Content-Disposition"] = f"attachment; filename={gid}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/exams/<token>/<gid>/hardreset", methods=["GET"])
@require_token(lambda: config.config.final_token)
def hardreset(gid: int, token: str):
    seed = db.seeds.get_final_seed(gid)
    if seed is not None and config.config.final_tasks:
        db.seeds.delete_final_seed(gid)
        db.statuses.delete_group_task_statuses(gid)
    return redirect(url_for("views.pre_exam", group_id=gid, token=token))


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
