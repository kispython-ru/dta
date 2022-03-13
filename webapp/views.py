import csv
import io
from typing import List, Union

from flask import Blueprint
from flask import current_app as app
from flask import make_response, render_template, request

from webapp.forms import MessageForm
from webapp.managers import AppDbContext, TaskStatusEnum
from webapp.models import Group, Task, TaskStatus, Variant
from webapp.utils import handle_errors, use_db


blueprint = Blueprint("views", __name__)


def find_task_status(
        statuses: List[TaskStatus],
        task: Task,
        variant: Variant,
        group: Group,
):
    for status in statuses:
        if status.group == group.id and status.variant == variant.id and status.task == task.id:
            return TaskStatusEnum(status.status).code
    return "–"


def get_real_ip() -> str:
    ip_forward_headers = request.headers.getlist("X-Forwarded-For")
    if ip_forward_headers:
        return ip_forward_headers[0]
    return request.remote_addr


@blueprint.route("/", methods=["GET"])
@handle_errors()
@use_db()
def dashboard(db: AppDbContext):
    groupings = db.groups.get_groupings()
    return render_template("dashboard.jinja", groupings=groupings)


@blueprint.route("/group/<group_id>", methods=["GET"])
@handle_errors()
@use_db()
def group(db: AppDbContext, group_id: int):
    group = db.groups.get_by_id(group_id)
    variants = db.variants.get_all()
    tasks = db.tasks.get_all()
    statuses = db.statuses.get_all()
    return render_template(
        "group.jinja",
        variants=variants,
        group=group,
        tasks=tasks,
        statuses=statuses,
        find_task_status=find_task_status,
    )


@blueprint.route(
    "/group/<group_id>/variant/<variant_id>/task/<task_id>",
    methods=["GET", "POST"],
)
@handle_errors()
@use_db()
def task(db: AppDbContext, group_id: int, variant_id: int, task_id: int):
    variant = db.variants.get_by_id(variant_id)
    group = db.groups.get_by_id(group_id)
    task = db.tasks.get_by_id(task_id)
    form = MessageForm()
    if form.validate_on_submit():
        code = form.code.data
        ip = get_real_ip()
        message = db.messages.submit_task(
            task_id, variant_id, group_id, code, ip)
        if message is None:
            raise ValueError("Unable to accept the submission.")
        status = db.statuses.submit_task(task_id, variant_id, group_id, code)
        return render_template(
            "success.jinja",
            form=form,
            variant=variant,
            group=group,
            task=task,
            status=status,
        )
    status = db.statuses.get_task_status(task_id, variant_id, group_id)
    status_enum = TaskStatusEnum(status.status) if status is not None else None
    return render_template(
        "task.jinja",
        form=form,
        variant=variant,
        group=group,
        task=task,
        status=status,
        status_enum=status_enum,
    )


@blueprint.route("/csv/<separator>/<token>/<count>", methods=["GET"])
@blueprint.route(
    "/csv/<separator>/<token>",
    methods=["GET"], defaults={"count": None},
)
@handle_errors(error_code=401)
@use_db()
def export(
    db: AppDbContext,
    separator: str,
    token: str,
    count: Union[int, None],
):
    configured_token = app.config["CSV_TOKEN"]
    if configured_token != token:
        raise ValueError("Access is denied.")
    messages = db.messages.get_all() if count is None else db.messages.get_latest(count)
    groups = db.groups.get_all()
    group_titles = {}
    for group in groups:
        group_titles[group.id] = group.title
    rows = [["ID", "Время", "Группа", "Задача", "Вариант", "IP", "Код"]]
    for message in messages:
        group_title = group_titles[message.group]
        time = message.time.strftime("%Y-%m-%d %H:%M:%S")
        task = message.task + 1
        rows.append([
            message.id,
            time,
            group_title,
            task,
            message.variant,
            message.ip,
            message.code,
        ])
    si = io.StringIO()
    delimiter = ";" if separator == "semicolon" else ","
    cw = csv.writer(si, delimiter=delimiter)
    cw.writerows(rows)
    bom = u"\uFEFF"
    value = bom + si.getvalue()
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output
