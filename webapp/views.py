from typing import Union

from flask import Blueprint
from flask import current_app as app
from flask import make_response, render_template, request

from webapp.forms import MessageForm
from webapp.managers import ExportManager, find_task_status
from webapp.repositories import AppDatabase, TaskStatusEnum
from webapp.utils import get_real_ip, handle_errors


blueprint = Blueprint("views", __name__)
db = AppDatabase(lambda: app.config["CONNECTION_STRING"])
exports = ExportManager(db.groups, db.messages)


@blueprint.route("/", methods=["GET"])
@handle_errors(error_code=404)
def dashboard():
    groupings = db.groups.get_groupings()
    return render_template("dashboard.jinja", groupings=groupings)


@blueprint.route("/group/<group_id>", methods=["GET"])
@handle_errors(error_code=404)
def group(group_id: int):
    group = db.groups.get_by_id(group_id)
    statuses = db.statuses.get_by_group(group.id)
    variants = db.variants.get_all()
    tasks = db.tasks.get_all()
    task_base_url = app.config["TASK_BASE_URL"]
    return render_template(
        "group.jinja",
        variants=variants,
        group=group,
        tasks=tasks,
        statuses=statuses,
        find_task_status=find_task_status,
        task_base_url=task_base_url,
    )


@blueprint.route(
    "/group/<gid>/variant/<vid>/task/<tid>",
    methods=["GET", "POST"]
)
@handle_errors(error_code=404)
def task(gid: int, vid: int, tid: int):
    variant = db.variants.get_by_id(vid)
    group = db.groups.get_by_id(gid)
    task = db.tasks.get_by_id(tid)
    status = db.statuses.get_task_status(tid, vid, gid)
    checked = status is not None and status.status == TaskStatusEnum.Checked
    form = MessageForm()
    if form.validate_on_submit() and not checked:
        code = form.code.data
        ip = get_real_ip(request)
        db.messages.submit_task(tid, vid, gid, code, ip)
        status = db.statuses.submit_task(tid, vid, gid, code)
        return render_template(
            "success.jinja",
            form=form,
            variant=variant,
            group=group,
            task=task,
            status=status,
        )
    task_base_url=app.config["TASK_BASE_URL"]
    return render_template(
        "task.jinja",
        form=form,
        variant=variant,
        group=group,
        task=task,
        status=status,
        task_base_url=task_base_url,
    )


@blueprint.route("/csv/<sep>/<token>/<count>", methods=["GET"])
@blueprint.route(
    "/csv/<sep>/<token>",
    methods=["GET"],
    defaults={"count": None}
)
@handle_errors(error_code=401)
def export(sep: str, token: str, count: Union[int, None]):
    if app.config["CSV_TOKEN"] != token:
        raise ValueError("Access is denied.")
    value = exports.export_messages(count, sep)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output
