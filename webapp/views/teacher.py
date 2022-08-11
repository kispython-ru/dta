from flask_jwt_extended import create_access_token, jwt_required, set_access_cookies
from flask_jwt_extended.exceptions import JWTExtendedException

from flask import Blueprint
from flask import current_app as app
from flask import make_response, redirect, render_template, request, url_for

from webapp.forms import LoginForm
from webapp.managers import AppConfigManager, ExportManager, StatusManager, TeacherManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, require_token


blueprint = Blueprint("teacher", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
exports = ExportManager(db.groups, db.messages, statuses, db.variants, db.tasks)
teachers = TeacherManager(db.teachers)


@blueprint.route("/admin/login", methods=['GET', 'POST'])
def authorize():
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


@blueprint.route("/admin", methods=["GET"])
@jwt_required()
def dashboard():
    return "SECRET PAGE"


@blueprint.route("/csv/<s>/<token>/<count>", methods=["GET"])
@blueprint.route("/csv/<s>/<token>", methods=["GET"], defaults={"count": None})
def export(s: str, token: str, count: int | None):
    if config.config.csv_token != token:
        raise ValueError("Access is denied.")
    value = exports.export_messages(count, s)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/exams/<token>", methods=["GET"])
@require_token(lambda: config.config.final_token)
def exams(token: str):
    groups = db.groups.get_all()
    return render_template("teacher/exams.jinja", groups=groups, token=token)


@blueprint.route("/exams/<token>", methods=["POST"])
@require_token(lambda: config.config.final_token)
def enter_exam_group(token: str):
    group_id = request.form.get('group')
    return redirect(url_for("views.pre_exam", group_id=group_id, token=token))


@blueprint.route("/exams/<token>/<group_id>", methods=["GET"])
@require_token(lambda: config.config.final_token)
def pre_exam(group_id: int, token: str):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template("teacher/exam.jinja", group=group, seed=seed, token=token)


@blueprint.route("/exams/<token>/<group_id>", methods=["POST"])
@require_token(lambda: config.config.final_token)
def exam(group_id: int, token: str):
    seed = db.seeds.get_final_seed(group_id)
    if seed is None and config.config.final_tasks:
        db.seeds.begin_final_test(group_id)
    elif seed.active:
        db.seeds.end_final_test(group_id)
    else:
        db.seeds.continue_final_test(group_id)
    seed = db.seeds.get_final_seed(group_id)
    group = db.groups.get_by_id(group_id)
    return render_template("teacher/exam.jinja", group=group, seed=seed, token=token)


@blueprint.route("/exams/<token>/<gid>/score_csv", methods=["POST"])
@require_token(lambda: config.config.final_token)
def score_csv(gid: int, token: str):
    delimiter = request.form.get('delimiter')
    value = exports.export_exam_results(gid, delimiter)
    output = make_response(value)
    output.headers["Content-Disposition"] = f"attachment; filename={gid}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/exams/<token>/<gid>/hardreset", methods=["GET"])
@require_token(lambda: config.config.final_token)
def hardreset(gid: int, token: str):
    seed = db.seeds.get_final_seed(gid)
    if seed is not None and config.config.final_tasks:
        db.seeds.delete_final_seed(gid)
        db.statuses.delete_group_task_statuses(gid)
    return redirect(url_for("views.pre_exam", group_id=gid, token=token))


@blueprint.errorhandler(Exception)
def handle_view_errors(e):
    print(get_exception_info())
    return render_template("error.jinja", redirect="/admin")


@blueprint.errorhandler(JWTExtendedException)
def handle_authorization_errors(e):
    return redirect('/admin/login')
