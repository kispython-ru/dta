from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from flask import Blueprint
from flask import current_app as app
from flask import redirect, render_template, request, abort

from webapp.forms import (
    AnonMessageForm,
    StudentChangePasswordForm,
    StudentLoginForm,
    StudentMessageForm,
    StudentRegisterForm
)
from webapp.managers import AppConfigManager, GroupManager, StatusManager, StudentManager
from webapp.models import Student
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip, student_jwt_optional, student_jwt_reset


blueprint = Blueprint("student", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants,
                         db.statuses, config, db.seeds, db.checks)
groups = GroupManager(config, db.groups, db.seeds)
students = StudentManager(config, db.students, db.mailers)


@blueprint.route("/", methods=["GET"])
@student_jwt_optional(db.students)
def dashboard(student: Student | None):
    groupings = groups.get_groupings()
    return render_template(
        "student/dashboard.jinja",
        groupings=groupings,
        registration=config.config.registration,
        exam=config.config.exam,
        student=student
    )


@blueprint.route("/submissions", methods=["GET"])
@student_jwt_optional(db.students)
def submissions(student: Student | None):
    if student is None:
        abort(401)
    submissions_statuses = statuses.get_submissions_statuses(student)
    return render_template(
        "student/submissions.jinja",
        submissions=submissions_statuses,
        student=student,
        highlight=config.config.highlight_syntax,
    )


@blueprint.route("/group/<group_id>", methods=["GET"])
@student_jwt_optional(db.students)
def group(student: Student | None, group_id: int):
    group = statuses.get_group_statuses(group_id)
    seed = db.seeds.get_final_seed(group_id)
    blocked = config.config.exam and seed is None
    return render_template(
        "student/group.jinja",
        group=group,
        blocked=blocked,
        registration=config.config.registration,
        student=student
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
@student_jwt_optional(db.students)
def task(student: Student | None, gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    form = StudentMessageForm() if config.config.registration else AnonMessageForm()
    return render_template(
        "student/task.jinja",
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        status=status,
        form=form,
        student=student,
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
@student_jwt_optional(db.students)
def submit_task(student: Student | None, gid: int, vid: int, tid: int):
    allowed = student is not None or not config.config.registration
    status = statuses.get_task_status(gid, vid, tid)
    form = StudentMessageForm() if config.config.registration else AnonMessageForm()
    valid = form.validate_on_submit()
    if valid and allowed and not status.disabled:
        if not config.config.registration or students.check_password(student.email, form.password.data):
            ip = get_real_ip(request)
            sid = student.id if student else None
            db.messages.submit_task(tid, vid, gid, form.code.data, ip, sid)
            db.statuses.submit_task(tid, vid, gid, form.code.data, ip)
            return render_template(
                "student/success.jinja",
                status=status,
                registration=config.config.registration,
                student=student
            )
        form.password.errors.append("Указан неправильный пароль.")
    return render_template(
        "student/task.jinja",
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        status=status,
        form=form,
        student=student,
    )


@blueprint.route("/login", methods=['GET', 'POST'])
@student_jwt_reset(config, "/login")
def login():
    form = StudentLoginForm()
    if not form.validate_on_submit():
        return render_template("student/login.jinja", form=form)
    error = students.login(form.login.data, form.password.data)
    if error:
        form.login.errors.append(error)
        return render_template("student/login.jinja", form=form)
    response = redirect("/")
    student = db.students.find_by_email(form.login.data)
    set_access_cookies(response, create_access_token(identity=student.id))
    return response


@blueprint.route("/register", methods=['GET', 'POST'])
@student_jwt_reset(config, "/register")
def register():
    form = StudentRegisterForm()
    if form.validate_on_submit():
        form.login.errors.append(students.register(form.login.data, form.password.data))
    return render_template("student/register.jinja", form=form)


@blueprint.route("/change-password", methods=['GET', 'POST'])
@student_jwt_reset(config, "/change-password")
def change_password():
    form = StudentChangePasswordForm()
    if form.validate_on_submit():
        form.login.errors.append(students.change_password(form.login.data, form.password.data))
    return render_template("student/password.jinja", form=form)


@blueprint.route("/logout", methods=['GET'])
def logout():
    response = redirect("/")
    unset_jwt_cookies(response)
    return response


@blueprint.app_template_filter('hide')
def hide_email(value: str):
    if '@' not in value:
        return value
    username, domain = value.split('@')
    length = len(username)
    if length == 1:
        return f'*@{domain}'
    repeat = min((length - 1), 10) * '*'
    return f'{username[0]}{repeat}@{domain}'


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
