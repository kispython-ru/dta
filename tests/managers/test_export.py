from tests.utils import arrange_task

from webapp.managers import AppConfigManager, ExportManager, StatusManager
from webapp.repositories import AppDatabase


def test_export(db: AppDatabase):
    c = AppConfigManager(lambda: dict())
    s = StatusManager(db.tasks, db.groups, db.variants, db.statuses, c, db.seeds, db.checks)
    e = ExportManager(db.groups, db.messages, s, db.variants, db.tasks, db.students)
    (group, variant, task) = arrange_task(db)

    code = "main = lambda x: x**42"
    m = db.messages.submit_task(task, variant, group, code, "127.0.0.1", None)
    table = e.export_messages(10, ',')

    assert str(m.id) in table
    assert code in table
    assert '127.0.0.1' in table
