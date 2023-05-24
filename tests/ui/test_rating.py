from tests.utils import get_tags, unique_int, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_groups_rating(db: AppDatabase, client: FlaskClient):
    group_title, _, _ = send_solution_to_tasks(db)

    resource = client.get(f'/rating/groups')
    html_rating = resource.get_data(as_text=True)
    tags = get_tags(html_rating, 'div', 'ms-2 me-auto')

    assert any(group_title in tag.get_text().strip() for tag in tags)


def test_students_rating(db: AppDatabase, client: FlaskClient):
    group_title, group_id, variant_id = send_solution_to_tasks(db)

    resource = client.get(f'/rating')
    html_rating = resource.get_data(as_text=True)
    tags = get_tags(html_rating, 'div', 'ms-2 me-auto')

    assert len(tags) == 1
    assert tags[0].get_text().strip() == f'{group_title}, вар. {variant_id + 1}'
    assert tags[0].fetchParents()[0].get('href') == f'/group/{group_id}'


def send_solution_to_tasks(db):
    group_id, group_title, tasks, variant_id = create_groups_and_tasks(db)
    # Сдача всех заданий в данной группе, с данным вариантом
    for task in tasks:
        db.statuses.submit_task(task.id, variant_id, group_id, unique_str(), unique_str())
        db.statuses.check(task.id, variant_id, group_id, unique_str(), True, unique_str(), unique_str())
    return group_title, group_id, variant_id


def create_groups_and_tasks(db):
    prefix = unique_str().replace('-', '')
    group_title = create_test_group(db, prefix)
    variant_id = create_test_variant(db)
    create_test_tasks(db)
    # Получение всех заданий
    tasks = db.tasks.get_all()
    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    return group_id, group_title, tasks, variant_id




def create_test_tasks(db):
    tasks_id = unique_int()
    db.tasks.create_by_ids([tasks_id])


def create_test_variant(db):
    variant_id = unique_int()
    db.variants.create_by_ids([variant_id])
    return variant_id


def create_test_group(db, prefix):
    group_title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([group_title])
    return group_title
