from secrets import token_hex

from tests.utils import arrange_task, unique_str

from webapp.repositories import AppDatabase


def test_get_by_student(db: AppDatabase):
    group_id, variant_id, task_id = arrange_task(db)

    student_email = f"{unique_str()}@test.ru"

    student = db.students.create(student_email, unique_str())
    db.students.confirm(student_email)
    db.students.update_group(student.id, group_id)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, student.id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    result = db.checks.get_by_student(student, 0, 10)

    assert len(result) == 1
    assert result[0][1].code == code
    assert result[0][1].ip == ip
    assert result[0][0].output == "test"


def test_count_student_submissions(db: AppDatabase):
    group_id, variant_id, task_id = arrange_task(db)

    student_email = f"{unique_str()}@test.ru"

    student = db.students.create(student_email, unique_str())
    db.students.confirm(student_email)
    db.students.update_group(student.id, group_id)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, student.id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    result = db.checks.count_student_submissions(student)

    assert result == 1


def test_count_submissions_by_info(db: AppDatabase):
    group_id, variant_id, task_id = arrange_task(db)

    student_email = f"{unique_str()}@test.ru"

    student = db.students.create(student_email, unique_str())
    db.students.confirm(student_email)
    db.students.update_group(student.id, group_id)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, student.id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    result = db.checks.count_submissions_by_info(group_id, variant_id, task_id, False)

    assert result == 1


def test_count_session_id_submissions(db: AppDatabase):
    group_id, variant_id, task_id = arrange_task(db)

    session_id = token_hex(16)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, None, session_id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    result = db.checks.count_session_id_submissions(session_id=session_id)

    assert result == 1


def test_get_by_session_id(db: AppDatabase):
    group_id, variant_id, task_id = arrange_task(db)

    session_id = token_hex(16)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, None, session_id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    result = db.checks.get_by_session_id(session_id=session_id, skip=0, take=10)

    assert len(result) == 1
    assert result[0][1].session_id == session_id
