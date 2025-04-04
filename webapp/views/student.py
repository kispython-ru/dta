import os
from secrets import token_hex

import requests
from authlib.integrations.requests_client import OAuth2Session
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from flask_jwt_extended.exceptions import JWTExtendedException
from flask_paginate import Pagination
from jwt.exceptions import PyJWTError

from flask import Blueprint, Response
from flask import current_app as app
from flask import redirect, render_template, request, send_from_directory

from webapp.forms import StudentChangePasswordForm, StudentLoginForm, StudentMessageForm, StudentRegisterForm
from webapp.managers import AppConfigManager, GroupManager, HomeManager, StatusManager, StudentManager
from webapp.models import Student, Variant
from webapp.repositories import AppDatabase, VariantRepository
from webapp.utils import authorize, get_exception_info, get_greeting_msg, get_real_ip, logout


blueprint = Blueprint("student", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds, db.checks)
home_manager = HomeManager(statuses)
groups = GroupManager(config, db.groups, db.seeds)
students = StudentManager(config, db.students, db.mailers)


@blueprint.after_request
def set_anonymous_identifier(response: Response) -> Response:
    if not config.config.registration and not request.cookies.get("anonymous_identifier"):
        response.set_cookie("anonymous_identifier", value=token_hex(16))
    return response


@blueprint.route("/", methods=["GET"])
@authorize(db.students)
def dashboard(student: Student | None):
    if config.config.registration and student and student.group is not None and student.variant is not None:
        return redirect("/home")
    if config.config.registration and not config.config.exam and student and student.group is not None and \
            student.variant is None:
        return redirect("/variant")
    groupings = groups.get_groupings()
    return render_template(
        "student/dashboard.jinja",
        groupings=groupings,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        student=student,
    )


@blueprint.route("/variant", methods=["GET"])
@authorize(db.students)
def variant(student: Student | None):
    if config.config.registration and not student:
        return redirect("/login")
    if config.config.registration and student and student.variant is not None:
        return redirect("/")
    all_variants: list[int] = list(variant_obj.id for variant_obj in db.variants.get_all())
    return render_template(
        "student/choice_of_variant.jinja",
        variants=all_variants,
        registration=config.config.registration,
        group_rating=config.config.groups,
        student=student,
    )


@blueprint.route("/submissions", methods=["GET"], defaults={'page': 0})
@blueprint.route("/submissions/<int:page>", methods=["GET"])
@authorize(db.students)
def submissions(student: Student | None, page: int):
    size = 5
    session = request.cookies.get("anonymous_identifier")
    if not config.config.enable_registration:
        if not session:
            return redirect('/')
        submissions = statuses.get_anonymous_submissions_statuses(session, (page - 1) * size, size)
        count = statuses.count_session_id_submissions(session)
    elif student is not None:
        submissions = statuses.get_submissions_statuses(student, (page - 1) * size, size)
        count = statuses.count_student_submissions(student)
    else:
        return redirect('/')
    if not submissions and page > 0:
        return redirect(f"/submissions/{page - 1}")
    pagination = Pagination(
        page=page,
        per_page=size,
        total=count,
        search=False,
        prev_label="<",
        next_label=">",
        inner_window=2,
        outer_window=0,
        css_framework="bootstrap5",
    )
    return render_template(
        "student/submissions.jinja",
        submissions=submissions,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        student=student,
        highlight=config.config.highlight_syntax,
        page=page,
        pagination=pagination,
    )


@blueprint.route("/home", methods=["GET"])
@authorize(db.students)
def home(student: Student | None):
    if config.config.registration and not student:
        return redirect("/login")
    if config.config.exam:
        return redirect("/")
    if config.config.registration and student:
        if student.group is None:
            return redirect("/")
        elif student.variant is None:
            return redirect("/variant")
    group = statuses.get_group_statuses(student.group, False)
    tasks_statuses = list(int(task_status.status) for task_status in group.variants[student.variant].statuses)
    return render_template(
        "student/home.jinja",
        student=student,
        greeting_message=get_greeting_msg(),
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        group=group,
        variant=student.variant,
        variants=db.variants.get_all(),
        number_of_tasks=len(group.variants),
        tasks_statuses=tasks_statuses,
        group_place=home_manager.get_group_place(student.group),
        student_place=home_manager.get_student_place(student.group, student.variant),
    )


@blueprint.route("/home/variant_select", methods=["POST"])
@authorize(db.students)
def open_variant(student: Student):
    vid = request.form.get("variant")
    if vid and vid.isdigit():
        db.students.update_variant(student.id, vid)
    return redirect(f"/home")


@blueprint.route("/group/<int:gid>", methods=["GET"])
@authorize(db.students)
def group(student: Student | None, gid: int):
    if config.config.registration and not student:
        return redirect("/login")
    hide_pending = config.config.exam and request.args.get('hide_pending', False)
    group = statuses.get_group_statuses(gid, hide_pending)
    seed = db.seeds.get_final_seed(gid)
    blocked = config.config.exam and seed is None
    return render_template(
        "student/group.jinja",
        group=group,
        blocked=blocked,
        hide_pending=hide_pending,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        student=student,
    )


@blueprint.route("/group/select/<int:gid>", methods=["GET"])
@authorize(db.students, lambda _: True)
def group_select(student: Student, gid: int):
    if not student:
        return redirect("/login")
    if student.group is None:
        db.students.update_group(student.id, gid)
    return redirect("/variant")


@blueprint.route("/variant/select/<int:vid>", methods=["GET"])
@authorize(db.students, lambda _: True)
def variant_select(student: Student, vid: int):
    if not student:
        return redirect("/login")
    if student.group is None:
        return redirect("/")
    if student.variant is None:
        db.students.update_variant(student.id, vid)
    return redirect(f"/home")


@blueprint.route("/rating/groups", methods=["GET"])
@authorize(db.students)
def rating_groups(student: Student | None):
    groupings = statuses.get_group_rating()
    return render_template(
        "student/groups_rating.jinja",
        groupings=groupings,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        student=student,
    )


@blueprint.route("/rating", methods=["GET"])
@authorize(db.students)
def rating(student: Student | None):
    groupings = statuses.get_rating()
    return render_template(
        "student/rating.jinja",
        groupings=groupings,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        student=student,
    )


@blueprint.route("/group/<int:gid>/variant/<int:vid>/task/<int:tid>", methods=["GET"])
@authorize(db.students)
def task(student: Student | None, gid: int, vid: int, tid: int):
    if config.config.registration and not student:
        return redirect("/login")
    if student and not student.teacher and student.group != gid:
        return redirect("/")
    status = statuses.get_task_status(gid, vid, tid)
    form = StudentMessageForm()
    return render_template(
        "student/task.jinja",
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        status=status,
        form=form,
        student=student,
    )


@blueprint.route("/group/<int:gid>/variant/<int:vid>/task/<int:tid>", methods=["POST"])
@authorize(db.students)
def submit_task(student: Student | None, gid: int, vid: int, tid: int):
    if config.config.registration and not student:
        return redirect("/login")
    if student and not student.teacher and student.group != gid:
        return redirect("/")
    form = StudentMessageForm()
    valid = form.validate_on_submit()
    status = statuses.get_task_status(gid, vid, tid)
    ip = get_real_ip(request)
    if valid and not status.disabled and db.ips.is_allowed(ip):
        sid = student.id if student else None
        session_id = request.cookies.get("anonymous_identifier")
        db.messages.submit_task(tid, vid, gid, form.code.data, ip, sid, session_id)
        db.statuses.submit_task(tid, vid, gid, form.code.data, ip)
        return render_template(
            "student/success.jinja",
            status=status,
            registration=config.config.registration,
            group_rating=config.config.groups,
            exam=config.config.exam,
            student=student,
        )
    return render_template(
        "student/task.jinja",
        highlight=config.config.highlight_syntax,
        registration=config.config.registration,
        group_rating=config.config.groups,
        exam=config.config.exam,
        status=status,
        form=form,
        student=student,
    )


@blueprint.route("/files/task/<int:tid>/group/<int:gid>", methods=["GET"])
@authorize(db.students)
def files(student: Student | None, tid: int, gid: int):
    if config.config.registration and not student:
        return redirect("/login")
    if student and not student.teacher and student.group != gid:
        return redirect("/")
    group = db.groups.get_by_id(gid)
    title = group.external or group.title
    path = os.path.join(str(tid), f'{title}.html')
    return send_from_directory(config.config.task_base_path, path)


@blueprint.route("/login", methods=['GET', 'POST'])
@logout(config, "/login", False)
def login():
    form = StudentLoginForm(lks_oauth_enabled=config.config.enable_lks_oauth)
    if not form.validate_on_submit():
        return render_template(
            "student/login.jinja",
            registration=config.config.registration,
            group_rating=config.config.groups,
            form=form
        )
    error = students.login(form.login.data, form.password.data)
    if error:
        form.login.errors.append(error)
        return render_template(
            "student/login.jinja",
            registration=config.config.registration,
            group_rating=config.config.groups,
            form=form
        )
    student = db.students.find_by_email(form.login.data)
    response = redirect("/")
    set_access_cookies(response, create_access_token(identity=student.id))
    return response


@blueprint.route("/login/lks", methods=["GET", "POST"])
@logout(config, "/login/lks")
def login_with_lks():
    if not config.config.enable_lks_oauth:
        return redirect("/")
    auth_ep = f'{config.config.lks_api_base_url}/oauth2/v1/authorize'
    oauth = OAuth2Session(
        config.config.lks_oauth_client_id,
        config.config.lks_oauth_client_secret,
        scope='basic')
    uri, _ = oauth.create_authorization_url(auth_ep)
    return redirect(uri)


@blueprint.route("/login/lks/callback", methods=["GET", "POST"])
@logout(config, "/login/lks/callback")
def login_with_lks_callback():
    if not config.config.enable_lks_oauth:
        return redirect("/")
    token_ep = f'{config.config.lks_api_base_url}/oauth2/v1/token/'
    userinfo_ep = f'{config.config.lks_api_base_url}/resources/v1/userinfo'
    oauth = OAuth2Session(
        config.config.lks_oauth_client_id,
        config.config.lks_oauth_client_secret,
        scope='basic')
    response = oauth.fetch_token(token_ep, authorization_response=request.url)
    access_token = response['access_token']
    info = requests.get(userinfo_ep, headers={'Authorization': f'Bearer {access_token}'}).json()
    email = info['username']
    if not email:
        return redirect("/")
    student = db.students.get_by_external_email(email, 'lks')
    if not student:
        student = db.students.find_by_email(email)
        if not student:
            student = db.students.create_external(email, 'lks')
    response = redirect("/")
    set_access_cookies(response, create_access_token(identity=student.id))
    return response


@blueprint.route("/register", methods=["GET", "POST"])
@logout(config, "/register")
def register():
    form = StudentRegisterForm(lks_oauth_enabled=config.config.enable_lks_oauth)
    if form.validate_on_submit():
        form.login.errors.append(students.register(form.login.data, form.password.data))
    return render_template(
        "student/register.jinja",
        registration=config.config.registration,
        group_rating=config.config.groups,
        form=form
    )


@blueprint.route("/change-password", methods=['GET', 'POST'])
@logout(config, "/change-password")
def change_password():
    form = StudentChangePasswordForm()
    if form.validate_on_submit():
        form.login.errors.append(students.change_password(form.login.data, form.password.data))
    return render_template(
        "student/password.jinja",
        registration=config.config.registration,
        group_rating=config.config.groups,
        form=form
    )


@blueprint.route("/logout", methods=['GET'])
def do_logout():
    response = redirect("/")
    unset_jwt_cookies(response)
    return response


@blueprint.app_template_filter('hide')
def hide_email_filter(value: str):
    return students.hide_email(value)


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
