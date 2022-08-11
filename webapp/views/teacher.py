from flask_jwt_extended import create_access_token, jwt_required, set_access_cookies, verify_jwt_in_request, unset_jwt_cookies
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from flask import Blueprint
from flask import current_app as app
from flask import make_response, redirect, render_template, request

from webapp.forms import LoginForm
from webapp.managers import AppConfigManager, ExportManager, StatusManager, TeacherManager
from webapp.models import Group, Message, Status
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info


blueprint = Blueprint("teacher", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
exports = ExportManager(db.groups, db.messages, statuses, db.variants, db.tasks)
teachers = TeacherManager(db.teachers)


@blueprint.route("/admin/login", methods=['GET', 'POST'])
def login():
    if verify_jwt_in_request(True):
        return redirect('/admin')
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("teacher/login.jinja", form=form)
    teacher = teachers.check_password(form.login.data, form.password.data)
    if teacher is None:
        return render_template("teacher/login.jinja", form=form)
    access = create_access_token(identity=teacher.id)
    response = redirect("/admin")
    set_access_cookies(response, access)
    return response


@blueprint.route("/admin/logout", methods=['GET'])
def logout():
    response = redirect("/admin/login")
    unset_jwt_cookies(response)
    return response


@blueprint.route("/admin", methods=["GET"])
@jwt_required()
def dashboard():
    groups = db.groups.get_all()
    return render_template("teacher/dashboard.jinja", groups=groups)


@blueprint.route("/admin/group/select", methods=["GET"])
@jwt_required()
def select_group():
    group = request.args.get('group')
    if config.config.final_tasks is not None:
        return redirect(f'/admin/group/{group}/exam')
    return redirect(f'/admin/group/{group}')


@blueprint.route("/admin/group/<group_id>/exam", methods=["GET"])
@jwt_required()
def exam(group_id: int):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template("teacher/exam.jinja", group=group, seed=seed)


@blueprint.route("/admin/group/<group_id>/exam/toggle", methods=["GET"])
@jwt_required()
def exam_toggle(group_id: int):
    seed = db.seeds.get_final_seed(group_id)
    if seed is None and config.config.final_tasks:
        db.seeds.begin_final_test(group_id)
    elif seed is not None and seed.active:
        db.seeds.end_final_test(group_id)
    elif seed is not None:
        db.seeds.continue_final_test(group_id)
    return redirect(f'/admin/group/{group_id}/exam')


@blueprint.route("/admin/group/<group_id>/exam/csv", methods=["GET"])
@jwt_required()
def exam_csv(group_id: int):
    delimiter = request.args.get('delimiter')
    value = exports.export_exam_results(group_id, delimiter)
    output = make_response(value)
    output.headers["Content-Disposition"] = f"attachment; filename={group_id}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/admin/messages", methods=["GET"])
@jwt_required()
def messages():
    separator = request.args.get('separator')
    count = request.args.get('count')
    value = exports.export_messages(count, separator)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/admin/group/<group_id>", methods=["GET"])
@jwt_required()
def queue(group_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_next_pending_message()
    if message is None or group.id == message.group:
        return render_template("teacher/queue.jinja", group=group, message=message)
    return redirect(f'/admin')


@blueprint.route("/admin/group/<group_id>/queue/<message_id>/accept", methods=["GET"])
@jwt_required()
def accept(group_id: int, message_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_by_id(message_id)
    if group.id == message.group:
        process_message(message, Status.Checked, None)
    return redirect(f"/admin/group/{group_id}")


@blueprint.route("/admin/group/<group_id>/queue/<message_id>/reject", methods=["GET"])
def reject(group_id: int, message_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_by_id(message_id)
    if group.id == message.group:
        comment = request.args.get("comment")
        process_message(message, Status.Failed, comment)
    return redirect(f"/admin/group/{group_id}")


def process_message(message: Message, status: Status, comment: str | None):
    db.messages.mark_as_processed(message.id)
    db.statuses.update_status(
        task=message.task,
        variant=message.variant,
        group=message.group,
        code=message.code,
        status=status,
        ip=message.ip,
        output=comment,
    )
    db.checks.record_check(
        message=message.id,
        status=status,
        output=comment,
    )


@blueprint.errorhandler(Exception)
def handle_view_errors(e):
    print(get_exception_info())
    return render_template("error.jinja", redirect="/admin")


@blueprint.errorhandler(JWTExtendedException)
@blueprint.errorhandler(PyJWTError)
def handle_authorization_errors(e):
    response = redirect('/admin/login')
    unset_jwt_cookies(response)
    return response
