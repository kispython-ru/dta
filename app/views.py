from flask import Blueprint, render_template, redirect, make_response
from flask import current_app as app
from flask_jwt_extended.utils import get_jwt_identity, unset_jwt_cookies
from sqlalchemy.orm.session import Session
from app.utils import authorize, handle_errors, use_session
from app.forms import LoginForm, RegisterForm
from app.managers import TaskManager, UserManager
from flask_jwt_extended import create_access_token, set_access_cookies

blueprint = Blueprint('views', __name__)


@blueprint.route("/register", methods=['GET', 'POST'])
@authorize(redirect_if_authorized=True, redirect_url="/")
@handle_errors(error_message="Unable to register.", error_redirect="/register")
@use_session()
def register(session: Session):
    form = RegisterForm()
    if form.validate_on_submit():
        users = UserManager(session)
        user = users.register(form.email.data, form.password.data)
        access_token = create_access_token(identity=user.id)
        response = make_response(redirect("/"))
        set_access_cookies(response, access_token)
        return response
    app.logger.info(f"Registration form is invalid: {form.errors}")
    return render_template("anon/register.jinja", form=form)


@blueprint.route("/login", methods=['GET', 'POST'])
@authorize(redirect_if_authorized=True, redirect_url="/")
@handle_errors(error_message="Unable to log in.", error_redirect="/login")
@use_session()
def login(session: Session):
    form = LoginForm()
    if form.validate_on_submit():
        users = UserManager(session)
        user = users.check_password(form.email.data, form.password.data)
        if user is not None:
            access_token = create_access_token(identity=user.id)
            response = make_response(redirect("/"))
            set_access_cookies(response, access_token)
            return response
        return render_template(
            "error.jinja",
            error_code=401,
            error_message="Password is invalid.",
            error_redirect="/login")
    app.logger.info(f"Login form is invalid: {form.errors}")
    return render_template("anon/login.jinja", form=form)


@blueprint.route("/logout", methods=["GET"])
@handle_errors()
def logout():
    response = make_response(redirect("/login"))
    unset_jwt_cookies(response)
    return response


@blueprint.route("/", methods=['GET'])
@authorize()
@handle_errors()
@use_session()
def tasks(session: Session):
    users = UserManager(session)
    tasks = TaskManager(session)
    id = get_jwt_identity()
    user = users.get_by_id(id)
    tasks = tasks.ensure_user_tasks_created(user.id)
    return render_template("user/tasks.jinja", user=user, tasks=tasks)


@blueprint.route("/tasks/<task_id>", methods=['GET'])
@authorize()
@handle_errors()
@use_session()
def task(session: Session, task_id: int):
    users = UserManager(session)
    tasks = TaskManager(session)
    id = get_jwt_identity()
    user = users.get_by_id(id)
    task = tasks.get_user_task(task_id, id)
    return render_template("user/task.jinja", user=user, info=task)
