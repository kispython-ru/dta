from typing import List
from flask import Blueprint, render_template
from app.forms import MessageForm
from app.managers import AppDbContext, TaskStatusEnum
from app.models import Group, Task, TaskStatus, Variant
from app.utils import handle_errors, use_session
from sqlalchemy.orm import Session
from flask import request

blueprint = Blueprint('views', __name__)

def find_task_status(statuses: List[TaskStatus], task: Task, variant: Variant, group: Group):
    for status in statuses:
        if status.group == group.id and status.variant == variant.id and status.task == task.id:
            return TaskStatusEnum(status.status).code
    return "—"


@blueprint.route("/", methods=['GET'])
@handle_errors()
@use_session()
def dashboard(session: Session):
    db = AppDbContext(session)
    groups = db.groups.get_all()
    return render_template(
        "dashboard.jinja",
        groups=groups,
        find_task_status=find_task_status)


@blueprint.route("/group/<group_id>", methods=['GET'])
@handle_errors()
@use_session()
def group(session: Session, group_id: int):
    db = AppDbContext(session)
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
        find_task_status=find_task_status)


@blueprint.route("/group/<group_id>/variant/<variant_id>/task/<task_id>",
                 methods=['GET', 'POST'])
@handle_errors()
@use_session()
def task(session: Session, group_id: int, variant_id: int, task_id: int):
    db = AppDbContext(session)
    variant = db.variants.get_by_id(variant_id)
    group = db.groups.get_by_id(group_id)
    task = db.tasks.get_by_id(task_id)
    form = MessageForm()
    if form.validate_on_submit():
        code = form.code.data
        ip = request.remote_addr
        message = db.messages.submit_task(task_id, variant_id, group_id, code, ip)
        if message is None:
            raise ValueError("Unable to accept the submission.")
        status = db.statuses.submit_task(task_id, variant_id, group_id, code)
        return render_template(
            "success.jinja",
            form=form,
            variant=variant,
            group=group,
            task=task,
            status=status)
    status = db.statuses.get_task_status(task_id, variant_id, group_id)
    status_enum = TaskStatusEnum(status.status) if status is not None else None
    return render_template(
        "task.jinja",
        form=form,
        variant=variant,
        group=group,
        task=task,
        status=status,
        status_enum=status_enum)
