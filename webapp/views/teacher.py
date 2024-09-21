from flask_jwt_extended import unset_jwt_cookies
from flask_jwt_extended.exceptions import JWTExtendedException
from flask_paginate import Pagination
from jwt.exceptions import PyJWTError

from flask import Blueprint
from flask import current_app as app
from flask import make_response, redirect, render_template, request

from webapp.managers import AppConfigManager, ExportManager, StatusManager, StudentManager
from webapp.models import Message, Student
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, teacher_jwt_required


blueprint = Blueprint("teacher", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

students = StudentManager(config, db.students, db.mailers)
statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds, db.checks)
exports = ExportManager(db.groups, db.messages, statuses, db.variants, db.tasks, db.students, students)


@blueprint.route("/teacher/submissions/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"], defaults={'page': 0})
@blueprint.route("/teacher/submissions/group/<gid>/variant/<vid>/task/<tid>/<int:page>", methods=["GET"])
@teacher_jwt_required(db.students)
def teacher_submissions(teacher: Student, gid: int, vid: int, tid: int, page: int):
    size = 5
    submissions_statuses = statuses.get_submissions_statuses_by_info(gid, vid, tid, (page - 1) * size, size)
    if not submissions_statuses and page > 0:
        return redirect(f"/teacher/submissions/group/{gid}/variant/{vid}/task/{tid}/{page - 1}")
    submissions_count = statuses.count_submissions_by_info(gid, vid, tid)
    pagination = Pagination(
        page=page,
        per_page=size,
        total=submissions_count,
        search=False,
        prev_label="<",
        next_label=">",
        inner_window=2,
        outer_window=0,
        css_framework="bootstrap5",
    )
    return render_template(
        "teacher/submissions.jinja",
        submissions=submissions_statuses,
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        group_rating=config.config.groups,
        page=page,
        info=(gid, vid, tid),
        pagination=pagination,
        student=teacher,
    )


@blueprint.route("/teacher/submissions", methods=["GET"])
@teacher_jwt_required(db.students)
def select_submissions(teacher: Student):
    gid = request.args.get('gid')
    vid = request.args.get('vid')
    tid = request.args.get('tid')
    return redirect(f'/teacher/submissions/group/{gid}/variant/{vid}/task/{tid}')


@blueprint.route("/teacher", methods=["GET"])
@teacher_jwt_required(db.students)
def dashboard(teacher: Student):
    groups = db.groups.get_all() if config.config.no_background_worker or config.config.final_tasks else None
    glist = db.groups.get_all()
    vlist = db.variants.get_all()
    tlist = db.tasks.get_all()
    ips = db.ips.list_allowed()
    return render_template(
        "teacher/dashboard.jinja",
        student=teacher,
        clearable=config.config.clearable_database,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        groups=groups,
        glist=glist,
        vlist=vlist,
        tlist=tlist,
        ips=ips,
    )


@blueprint.route("/teacher/group/select", methods=["GET"])
@teacher_jwt_required(db.students)
def select_group(teacher: Student):
    group = request.args.get('group')
    if config.config.exam:
        return redirect(f'/teacher/group/{group}/exam')
    return redirect(f'/teacher/group/{group}')


@blueprint.route("/teacher/group/<group_id>/rename", methods=["GET"])
@teacher_jwt_required(db.students)
def rename(teacher: Student, group_id: int):
    group = db.groups.get_by_id(group_id)
    title = request.args.get('title')
    db.groups.rename(group_id, title if title else group.external)
    return redirect(f'/teacher/group/{group_id}/exam')


@blueprint.route("/teacher/group/<group_id>/exam", methods=["GET"])
@teacher_jwt_required(db.students)
def exam(teacher: Student, group_id: int):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template(
        "teacher/exam.jinja",
        registration=config.config.registration,
        group_rating=config.config.groups,
        group=group,
        seed=seed,
        student=teacher
    )


@blueprint.route("/teacher/group/<group_id>/exam/toggle", methods=["GET"])
@teacher_jwt_required(db.students)
def exam_toggle(teacher: Student, group_id: int):
    seed = db.seeds.get_final_seed(group_id)
    if seed is None and config.config.final_tasks:
        db.seeds.begin_final_test(group_id)
    elif seed is not None and seed.active:
        db.seeds.end_final_test(group_id)
    elif seed is not None:
        db.seeds.continue_final_test(group_id)
    return redirect(f'/teacher/group/{group_id}/exam')


@blueprint.route("/teacher/exam/start", methods=["GET"])
@teacher_jwt_required(db.students)
def exam_startall(teacher: Student):
    groups = db.groups.get_all()
    for group in groups:
        seed = db.seeds.get_final_seed(group.id)
        if seed is None and config.config.final_tasks:
            db.seeds.begin_final_test(group.id)
        elif seed is not None:
            db.seeds.continue_final_test(group.id)
    return redirect('/teacher')


@blueprint.route("/teacher/exam/start/many", methods=["POST"])
@teacher_jwt_required(db.students)
def exam_startmany(teacher: Student):
    for id in request.form.getlist('groups'):
        id = int(id)
        seed = db.seeds.get_final_seed(id)
        if seed is None and config.config.final_tasks:
            db.seeds.begin_final_test(id)
        elif seed is not None:
            db.seeds.continue_final_test(id)
    return redirect('/teacher')


@blueprint.route("/teacher/exam/end", methods=["GET"])
@teacher_jwt_required(db.students)
def exam_endall(teacher: Student):
    groups = db.groups.get_all()
    for group in groups:
        db.seeds.end_final_test(group.id)
    return redirect('/teacher')


@blueprint.route("/teacher/exam/delete", methods=["GET"])
@teacher_jwt_required(db.students)
def exam_deleteall(teacher: Student):
    if not config.config.final_tasks or not config.config.clearable_database:
        return redirect('/teacher')
    groups = db.groups.get_all()
    for group in groups:
        db.statuses.delete_group_task_statuses(group.id)
        db.seeds.delete_final_seed(group.id)
    return redirect('/teacher')


@blueprint.route("/teacher/group/<group_id>/exam/delete", methods=["GET"])
@teacher_jwt_required(db.students)
def exam_delete(teacher: Student, group_id: int):
    if not config.config.final_tasks or not config.config.clearable_database:
        return redirect(f'/teacher/group/{group_id}/exam')
    db.statuses.delete_group_task_statuses(group_id)
    db.seeds.delete_final_seed(group_id)
    return redirect(f'/teacher/group/{group_id}/exam')


@blueprint.route("/teacher/group/<group_id>/exam/csv", methods=["GET"])
@teacher_jwt_required(db.students)
def exam_csv(teacher: Student, group_id: int):
    delimiter = request.args.get('delimiter')
    value = exports.export_exam_results(group_id, delimiter)
    output = make_response(value)
    output.headers["Content-Disposition"] = f"attachment; filename={group_id}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/teacher/messages", methods=["GET"])
@teacher_jwt_required(db.students)
def messages(teacher: Student):
    separator = request.args.get('separator')
    count = request.args.get('count')
    value = exports.export_messages(count, separator)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/teacher/group/<group_id>", methods=["GET"])
@teacher_jwt_required(db.students)
def queue(teacher: Student, group_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_next_pending_message()
    matches = message is None or group.id == message.group
    if matches and config.config.no_background_worker:
        return render_template(
            "teacher/queue.jinja",
            registration=config.config.registration,
            group_rating=config.config.groups,
            group=group,
            message=message,
            student=teacher
        )
    return redirect(f'/teacher')


@blueprint.route("/teacher/group/<group_id>/queue/<message_id>/accept", methods=["GET"])
@teacher_jwt_required(db.students)
def accept(teacher: Student, group_id: int, message_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_by_id(message_id)
    if group.id == message.group and config.config.no_background_worker:
        process_message(message, True, None)
    return redirect(f"/teacher/group/{group_id}")


@blueprint.route("/teacher/group/<group_id>/queue/<message_id>/reject", methods=["GET"])
@teacher_jwt_required(db.students)
def reject(teacher: Student, group_id: int, message_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_by_id(message_id)
    if group.id == message.group and config.config.no_background_worker:
        comment = request.args.get("comment")
        process_message(message, False, comment)
    return redirect(f"/teacher/group/{group_id}")


@blueprint.route("/teacher/ips/allow", methods=["GET"])
@teacher_jwt_required(db.students)
def allow_ip(teacher: Student):
    ip = request.args.get('ip')
    label = request.args.get('label')
    db.ips.allow(ip, label)
    return redirect("/teacher")


@blueprint.route("/teacher/ips/disallow/<int:id>", methods=["GET"])
@teacher_jwt_required(db.students)
def disallow_ip(teacher: Student, id: int):
    db.ips.disallow(id)
    return redirect("/teacher")


@blueprint.errorhandler(Exception)
def handle_view_errors(e):
    print(get_exception_info())
    return render_template("error.jinja", redirect="/")


@blueprint.errorhandler(JWTExtendedException)
@blueprint.errorhandler(PyJWTError)
def handle_authorization_errors(e):
    response = redirect('/login')
    unset_jwt_cookies(response)
    return response


def process_message(message: Message, ok: bool, comment: str | None):
    db.messages.mark_as_processed(message.id)
    status = db.statuses.check(
        task=message.task,
        variant=message.variant,
        group=message.group,
        code=message.code,
        ok=ok,
        output=comment,
        ip=message.ip,
    )
    db.checks.record_check(
        message=message.id,
        status=status.status,
        output=comment,
    )
