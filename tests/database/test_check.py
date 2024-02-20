from tests.utils import arrange_task, unique_str

from webapp.models import Student, TaskStatus
from webapp.repositories import AppDatabase


def test_get_quantity_by_student(db: AppDatabase):
    group_id, variant_id, task_id = arrange_task(db)

    student_email = f"{unique_str()}@test.ru"

    student = db.students.create(student_email, unique_str())
    db.students.confirm(student_email)
    db.students.update_group(db.students.find_by_email(student_email), group_id)

    code = "main = lambda: 42"
    ip = "0.0.0.0"

    message = db.messages.submit_task(task_id, variant_id, group_id, code, ip, student.id)
    stat = db.statuses.submit_task(task_id, variant_id, group_id, code, ip)
    db.checks.record_check(message.id, stat.status, "test")

    result = db.checks.get_quantity_by_student(student)

    assert result == 1
