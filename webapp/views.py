from asyncio import tasks
import csv
import functools
from typing import Union

from werkzeug.exceptions import HTTPException

from flask import Blueprint
from flask import current_app as app
from flask import make_response, redirect, render_template, request, url_for

from webapp.forms import MessageForm
from webapp.managers import AppConfigManager, ExportManager, StatusManager
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, get_real_ip


blueprint = Blueprint("views", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)
exports = ExportManager(db.groups, db.messages)
statuses = StatusManager(
    tasks=db.tasks,
    groups=db.groups,
    variants=db.variants,
    statuses=db.statuses,
    config=config,
    seeds=db.seeds
)


def require_final_token():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(kwargs) == 0 or config.config.final_token \
                                   != kwargs['token']:
                return render_template(
                       "error.jinja",
                       error_code=401,
                       error_message="Unauthorized",
                       error_redirect="/",
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


@blueprint.route("/", methods=["GET"])
def dashboard():
    groupings = db.groups.get_groupings()
    return render_template("dashboard.jinja", groupings=groupings)


@blueprint.route("/group/<group_id>", methods=["GET"])
def group(group_id: int):
    group = statuses.get_group_statuses(group_id)
    return render_template("group.jinja", group=group)


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["GET"])
def task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    highlight = config.config.highlight_syntax
    return render_template(
        "task.jinja",
        status=status,
        form=MessageForm(),
        highlight=highlight,
    )


@blueprint.route("/group/<gid>/variant/<vid>/task/<tid>", methods=["POST"])
def submit_task(gid: int, vid: int, tid: int):
    status = statuses.get_task_status(gid, vid, tid)
    form = MessageForm()
    valid = form.validate_on_submit()
    if valid and not status.checked and status.external.active:
        code = form.code.data
        db.messages.submit_task(tid, vid, gid, code, get_real_ip(request))
        db.statuses.submit_task(tid, vid, gid, code)
        return render_template("success.jinja", status=status)
    highlight = config.config.highlight_syntax
    return render_template(
        "task.jinja",
        status=status,
        form=form,
        highlight=highlight,
    )


@blueprint.route("/csv/<s>/<token>/<count>", methods=["GET"])
@blueprint.route("/csv/<s>/<token>", methods=["GET"], defaults={"count": None})
def export(s: str, token: str, count: Union[int, None]):
    if config.config.csv_token != token:
        raise ValueError("Access is denied.")
    value = exports.export_messages(count, s)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/exams/<token>", methods=["GET"])
@require_final_token()
def exams(token: str):
    groups = db.groups.get_all()
    return render_template("exams.jinja", groups=groups, token=token)


@blueprint.route("/exams/<token>", methods=["POST"])
@require_final_token()
def enter_exam_group(token: str):
    group_id = request.form.get('group')
    return redirect(url_for("views.pre_exam", group_id=group_id, token=token))


@blueprint.route("/exams/<token>/<group_id>", methods=["GET"])
@require_final_token()
def pre_exam(group_id: int, token: str):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template("exam.jinja", group=group, seed=seed, token=token)


@blueprint.route("/exams/<token>/<group_id>", methods=["POST"])
@require_final_token()
def exam(group_id: int, token: str):
    seed = db.seeds.get_final_seed(group_id)
    if seed is None:
        db.seeds.begin_final_test(group_id)
    elif seed.active:
        db.seeds.end_final_test(group_id)
    seed = db.seeds.get_final_seed(group_id)
    group = db.groups.get_by_id(group_id)
    return render_template("exam.jinja", group=group, seed=seed, token=token)


@blueprint.route("/exams/<token>/<group_id>/score_csv", methods=["POST"])
@require_final_token()
def score_csv(group_id: int, token: str):
    seed = db.seeds.get_final_seed(group_id)
    group = db.groups.get_by_id(group_id)
    variants = db.variants.get_all()
    result_table = []
    headings = ['Сдающая_группа', 'Вариант', '№1_Группа', '№1_Вариант', '№1_Задача', '№1_Статус',
                '№2_Группа', '№2_Вариант', '№2_Задача', '№2_Статус', 'Сумма_баллов']
    result_table.append(headings)
    for variant in variants:
        group_title = db.groups.get_by_id(group_id).title
        #variant
        #tasks 1-2 for every variant
        external_task1_current_variant = statuses.get_task_status(group_id, variant.id, 1).external
        external_task2_current_variant = statuses.get_task_status(group_id, variant.id, 2).external
        #task 1
        external_task1_group_title = external_task1_current_variant.group_title
        external_task1_new_variant = external_task1_current_variant.variant
        external_task1_new_task = external_task1_current_variant.task
        external_task1_group_id = db.groups.get_group_id_by_name(external_task1_group_title)
        print(external_task1_group_id)
        external_task1_new_status = statuses.get_task_status(external_task1_group_id,
                                                             external_task1_new_variant,
                                                             external_task1_new_task
                                                            )
        #external_task1_new_status = 0
        #task 2
        external_task2_group_title = external_task2_current_variant.group_title
        external_task2_new_variant = external_task2_current_variant.variant
        external_task2_new_task = external_task2_current_variant.task
        external_task2_group_id = db.groups.get_group_id_by_name(external_task2_group_title)
        external_task2_new_status = statuses.get_task_status(external_task2_group_id,
                                                             external_task1_new_variant,
                                                             external_task2_new_task
                                                            )
        #external_task2_new_status = 0
        exam_score = external_task1_new_status + external_task2_new_status
        result_table.append([group_title, variant.id, external_task1_group_title, external_task1_new_variant,
                        external_task1_new_task, external_task1_new_status, external_task2_group_title,
                        external_task2_new_variant, external_task2_new_task, external_task2_new_status,
                        exam_score])
    print(result_table)
    with open('Итоги зачёта ' + group_title + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                        quotechar=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(result_table)
    return render_template("exam.jinja", group=group, seed=seed, token=token)


@blueprint.errorhandler(Exception)
def handle_views_errors(error):
    error_code = error.code if isinstance(error, HTTPException) else 500
    print(get_exception_info())
    return render_template(
        "error.jinja",
        error_code=error_code,
        error_message="Error has occured.",
        error_redirect="/",
    )
