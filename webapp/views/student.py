from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    unset_jwt_cookies,
    verify_jwt_in_request
)
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from flask import Blueprint
from flask import current_app as app
from flask import redirect, render_template, request

from webapp.forms import LoginForm, MessageForm
from webapp.managers import AppConfigManager, GroupManager, StatusManager, StudentManager
from webapp.models import Student
from webapp.repositories import AppDatabase, StudentRepository
from webapp.utils import get_exception_info, get_real_ip, student_jwt_optional


blueprint = Blueprint("student", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
groups = GroupManager(config, db.groups, db.seeds)
students = StudentManager(db.students)


@blueprint.route("/", methods=["GET"])
@student_jwt_optional(db.students)
def dashboard(student: Student | None):
    groupings = groups.get_groupings()
    exam = config.config.final_tasks is not None
    return render_template("student/dashboard.jinja", groupings=groupings, exam=exam, student=student)


@blueprint.route("/group/<group_id>", methods=["GET"])
@student_jwt_optional(db.students)
def group(student: Student | None, group_id: int):
    group = statuses.get_group_statuses(group_id)
    seed = db.seeds.get_final_seed(group_id)
    blocked = config.config.final_tasks and seed is None
    return render_template("student/group.jinja", group=group, blocked=blocked, student=student)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
@student_jwt_optional(db.students)
def task(student: Student | None, gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    highlight = config.config.highlight_syntax
    registration = config.config.enable_registration
    return render_template(
        "student/task.jinja",
        status=status,
        form=MessageForm(),
        highlight=highlight,
        student=student,
        registration=registration
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
@student_jwt_optional(db.students)
def submit_task(student: Student | None, gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    form = MessageForm()
    valid = form.validate_on_submit() and not status.checked
    available = status.external.active and not config.config.readonly
    allowed = student is not None or not config.config.enable_registration
    if valid and available and allowed:
        code = form.code.data
        ip = get_real_ip(request)
        db.messages.submit_task(tid, vid, gid, code, ip)
        db.statuses.submit_task(tid, vid, gid, code, ip)
        return render_template("student/success.jinja", status=status, student=student)
    highlight = config.config.highlight_syntax
    return render_template(
        "student/task.jinja",
        status=status,
        form=form,
        highlight=highlight,
        student=student,
    )


@blueprint.route("/login", methods=['GET', 'POST'])
def login():
    if not config.config.enable_registration:
        return redirect('/')
    if verify_jwt_in_request(True):
        return redirect('/')
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("student/login.jinja", form=form)
    teacher = students.check_password(form.login.data, form.password.data)
    if teacher is None:
        return render_template("student/login.jinja", form=form)
    access = create_access_token(identity=teacher.id)
    response = redirect("/")
    set_access_cookies(response, access)
    return response


@blueprint.route("/logout", methods=['GET'])
def logout():
    response = redirect("/")
    unset_jwt_cookies(response)
    return response


@blueprint.errorhandler(Exception)
def handle_view_errors(e):
    print(get_exception_info())
    return render_template("error.jinja", redirect="/teacher")


@blueprint.errorhandler(JWTExtendedException)
@blueprint.errorhandler(PyJWTError)
def handle_authorization_errors(e):
    response = redirect('/login')
    unset_jwt_cookies(response)
    return response
