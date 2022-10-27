from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from flask import Blueprint
from flask import current_app as app
from flask import redirect, render_template, request

from webapp.forms import MessageForm, StudentChangePasswordForm, StudentLoginForm, StudentRegisterForm
from webapp.managers import AppConfigManager, GroupManager, StatusManager, StudentManager
from webapp.models import Student
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip, student_jwt_optional


blueprint = Blueprint("student", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
groups = GroupManager(config, db.groups, db.seeds)
students = StudentManager(db.students, db.mailers)


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
        if students.check_password(student.email, form.password.data):
            ip = get_real_ip(request)
            db.messages.submit_task(tid, vid, gid, form.code.data, ip)
            db.statuses.submit_task(tid, vid, gid, form.code.data, ip)
            return render_template("student/success.jinja", status=status, student=student)
        form.password.errors.append("Указан неправильный пароль.")
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
        response = redirect('/login')
        unset_jwt_cookies(response)
        return response
    form = StudentLoginForm()
    if not form.validate_on_submit():
        return render_template("student/login.jinja", form=form)
    if not students.exists(form.login.data):
        form.login.errors.append("Такой адрес почты не зарегистрирован!")
        return render_template("student/login.jinja", form=form)
    if not students.confirmed(form.login.data):
        form.login.errors.append(
            f"Пользователь не подтверждён! Отправьте пустое сообщение с Вашего адреса "
            f"электронной почты {form.login.data} на наш адрес {config.config.imap_login}"
            " для подтверждения Вашего аккаунта.")
        return render_template("student/login.jinja", form=form)
    student = students.check_password(form.login.data, form.password.data)
    if student is None:
        form.login.errors.append("Неправильный пароль.")
        return render_template("student/login.jinja", form=form)
    access = create_access_token(identity=student.id)
    response = redirect("/")
    set_access_cookies(response, access)
    return response


@blueprint.route("/register", methods=['GET', 'POST'])
def register():
    if not config.config.enable_registration:
        return redirect('/')
    if verify_jwt_in_request(True):
        response = redirect('/register')
        unset_jwt_cookies(response)
        return response
    form = StudentRegisterForm()
    if not form.validate_on_submit():
        return render_template("student/register.jinja", form=form)
    if students.exists(form.login.data):
        if not students.confirmed(form.login.data):
            form.login.errors.append(
                f"Пользователь не подтверждён! Отправьте пустое сообщение с Вашего адреса "
                f"электронной почты {form.login.data} на наш адрес {config.config.imap_login}"
                " для подтверждения.")
            return render_template("student/register.jinja", form=form)
        form.login.errors.append("Такой адрес почты уже зарегистрирован! Нажмите кнопку 'Войти'.")
        return render_template("student/register.jinja", form=form)
    if not students.email_allowed(form.login.data):
        domains = db.mailers.get_domains()
        desc = ", ".join(domains).rstrip().rstrip(',')
        form.login.errors.append(
            f'Данный поставщик услуг электронной почты не поддерживается. '
            f'Поддерживаемые поставщики: {desc}.')
        return render_template("student/register.jinja", form=form)
    students.create(form.login.data, form.password.data)
    form.login.errors.append(
        f"Вы успешно зарегистрировались, однако Ваш адрес электронной почты не подтверждён. "
        f"Отправьте пустое сообщение с Вашего адреса электронной почты {form.login.data} на "
        f"наш адрес {config.config.imap_login} для подтверждения."
    )
    return render_template("student/register.jinja", form=form)


@blueprint.route("/change-password", methods=['GET', 'POST'])
def change_password():
    if not config.config.enable_registration:
        return redirect('/')
    if verify_jwt_in_request(True):
        response = redirect('/change-password')
        unset_jwt_cookies(response)
        return response
    form = StudentChangePasswordForm()
    if not form.validate_on_submit():
        return render_template("student/password.jinja", form=form)
    if not students.exists(form.login.data):
        form.login.errors.append("Такой адрес почты не зарегистрирован!")
        return render_template("student/password.jinja", form=form)
    if not students.confirmed(form.login.data):
        form.login.errors.append(
            f"Пользователь не подтверждён! Отправьте пустое сообщение с Вашего адреса "
            f"электронной почты {form.login.data} на наш адрес {config.config.imap_login}"
            " для подтверждения.")
        return render_template("student/password.jinja", form=form)
    if not students.change_password(form.login.data, form.password.data):
        form.login.errors.append(f"Изменение пароля невозможно, обратитесь к администратору.")
        return render_template("student/password.jinja", form=form)
    form.login.errors.append(
        f"Запрос на изменение пароля создан! Отправьте пустое сообщение с Вашего адреса "
        f"электронной почты {form.login.data} на наш адрес {config.config.imap_login}"
        " для подтверждения операции изменения пароля.")
    return render_template("student/password.jinja", form=form)


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
