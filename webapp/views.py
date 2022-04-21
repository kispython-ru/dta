from typing import Union

import re

from werkzeug.exceptions import HTTPException

from flask import Blueprint, jsonify, redirect, url_for
from flask import current_app as app
from flask import make_response, render_template, request

from webapp.forms import MessageForm
from webapp.managers import AppConfigManager, ExportManager, StatusManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip


blueprint = Blueprint("views", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)
exports = ExportManager(db.groups, db.messages)
statuses = StatusManager(
    tasks=db.tasks,
    groups=db.groups,
    variants=db.variants,
    statuses=db.statuses,
    config=config,
    seeds=db.seeds
)


@blueprint.route("/", methods=["GET"])
def dashboard():
    groupings = db.groups.get_groupings()
    return render_template("dashboard.jinja", groupings=groupings)


@blueprint.route("/exams", methods=["GET"])
def exams():
    return render_template("exams.jinja")


@blueprint.route("/exams", methods=["POST"])
def enter_exam_group():
    group = request.form['group'].upper()
    print(group)
    pattern = r"[\u0401\u0451\u0410-\u044f]{4}-[0-9]{2}-[0-9]{2}"
    if re.match(pattern, group):
        group_id = db.groups.get_group_id_by_name(group)
        if group_id != None:
            return redirect(url_for("views.pre_exam", group_id=group_id))
        return render_template(
            "error.jinja",
            error_code = 404,
            error_message="Эта группа не сдаёт экзамен",
            error_redirect="/exams",
        )
    return render_template(
        "error.jinja",
        error_code = 404,
        error_message="Неверный формат ввода группы",
        error_redirect="/exams",
    )    


@blueprint.route("/exams/<group_id>", methods=["GET"])
def pre_exam(group_id: int):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template("exam.jinja", group=group, seed=seed)   


@blueprint.route("/exams/<group_id>", methods=["POST"])
def exam(group_id: int):
    seed = db.seeds.get_final_seed(group_id)
    if seed == None:
        db.seeds.begin_final_test(group_id)
    elif seed.active == True:
        db.seeds.end_final_test(group_id)
    seed = db.seeds.get_final_seed(group_id)    
    group = db.groups.get_by_id(group_id)
    return render_template("exam.jinja", group=group, seed=seed)


@blueprint.route("/group/<group_id>", methods=["GET"])
def group(group_id: int):
    group = statuses.get_group_statuses(group_id)
    return render_template("group.jinja", group=group)


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
