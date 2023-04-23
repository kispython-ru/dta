from authlib.integrations.requests_client import OAuth2Auth
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from flask import Blueprint, abort
from flask import current_app as app
from flask import redirect, render_template, request

from webapp.forms import StudentChangePasswordForm, StudentLoginForm, StudentMessageForm, StudentRegisterForm
from webapp.lks import lks_oauth_helper
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
        group_rating=config.config.groups,
        exam=config.config.exam,
        student=student,
    )


@blueprint.route("/submissions", methods=["GET"], defaults={'page': 0})
@blueprint.route("/submissions/<int:page>", methods=["GET"])
@student_jwt_optional(db.students)
def submissions(student: Student | None, page: int):
    if student is None:
        abort(401)
    size = 5
    submissions_statuses = statuses.get_submissions_statuses(student, page * size, size)
    if not submissions_statuses and page > 0:
        return redirect(f"/submissions/{page - 1}")
    return render_template(
        "student/submissions.jinja",
        submissions=submissions_statuses,
        registration=config.config.registration,
        group_rating=config.config.groups,
        student=student,
        highlight=config.config.highlight_syntax,
        page=page,
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
        group_rating=config.config.groups,
        student=student,
    )


@blueprint.route("/rating/groups", methods=["GET"])
@student_jwt_optional(db.students)
def rating_groups(student: Student | None):
    groupings = statuses.get_rating_data(is_group=True)
    return render_template(
        "student/groups_rating.jinja",
        groupings=groupings,
        registration=config.config.registration,
        group_rating=config.config.groups,
        student=student,
    )


@blueprint.route("/rating", methods=["GET"])
@student_jwt_optional(db.students)
def rating(student: Student | None):
    groupings = statuses.get_rating_data()
    return render_template(
        "student/rating.jinja",
        groupings=groupings,
        registration=config.config.registration,
        group_rating=config.config.groups,
        student=student,
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
@student_jwt_optional(db.students)
def task(student: Student | None, gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    form = StudentMessageForm()
    return render_template(
        "student/task.jinja",
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        group_rating=config.config.groups,
        status=status,
        form=form,
        student=student,
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
@student_jwt_optional(db.students)
def submit_task(student: Student | None, gid: int, vid: int, tid: int):
    allowed = student is not None or not config.config.registration
    status = statuses.get_task_status(gid, vid, tid)
    form = StudentMessageForm()
    valid = form.validate_on_submit()
    if valid and allowed and not status.disabled:
        ip = get_real_ip(request)
        sid = student.id if student else None
        db.messages.submit_task(tid, vid, gid, form.code.data, ip, sid)
        db.statuses.submit_task(tid, vid, gid, form.code.data, ip)
        return render_template(
            "student/success.jinja",
            status=status,
            registration=config.config.registration,
        group_rating=config.config.groups,
            student=student,
        )
    return render_template(
        "student/task.jinja",
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        group_rating=config.config.groups,
        status=status,
        form=form,
        student=student,
    )


@blueprint.route("/login", methods=['GET', 'POST'])
@student_jwt_reset(config, "/login")
def login():
    form = StudentLoginForm(lks_oauth_enabled=config.config.enable_lks_oauth)
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


@blueprint.route("/login/lks", methods=["GET", "POST"])
@student_jwt_reset(config, "/login/lks")
def login_with_lks():
    if not config.config.enable_lks_oauth:
        return redirect("/")
    client = lks_oauth_helper.oauth.create_client("lks")
    redirect_url = config.config.lks_redirect_url
    return client.authorize_redirect(redirect_url)


@blueprint.route("/login/lks/callback", methods=["GET", "POST"])
@student_jwt_reset(config, "/login/lks/callback")
def login_with_lks_callback():
    if not config.config.enable_lks_oauth:
        return redirect("/")
    client = lks_oauth_helper.oauth.create_client(lks_oauth_helper.name)
    token = client.authorize_access_token()
    auth = OAuth2Auth(token)
    user = lks_oauth_helper.get_me(auth)
    student = db.students.get_by_external(user.id, lks_oauth_helper.name)
    if student:
        db.students.update_group(student, user.academic_group)
    else:
        email = user.login
        student = db.students.find_by_email(email)
        if not student:
            student = db.students.create_external(
                email,
                user.id,
                user.academic_group,
                lks_oauth_helper.name,
            )
    response = redirect("/")
    set_access_cookies(response, create_access_token(identity=student.id))
    return response


@blueprint.route("/register", methods=["GET", "POST"])
@student_jwt_reset(config, "/register")
def register():
    form = StudentRegisterForm(lks_oauth_enabled=config.config.enable_lks_oauth)
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
    return render_template("error.jinja", redirect="/")


@blueprint.errorhandler(JWTExtendedException)
@blueprint.errorhandler(PyJWTError)
def handle_authorization_errors(e):
    response = redirect('/login')
    unset_jwt_cookies(response)
    return response
