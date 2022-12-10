from tests.utils import get_tags, unique_int, unique_str

from flask.testing import FlaskClient

from webapp.models import Status
from webapp.repositories import AppDatabase


def test_task_status_html_link(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    group_title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([group_title])

    variant_id = unique_int()
    db.variants.create_by_ids([variant_id])

    tasks_id = unique_int()
    db.tasks.create_by_ids([tasks_id])

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    db.statuses.submit_task(tasks_id, variant_id, group_id, unique_str(), unique_str())

    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tag_class = 'd-block text-center text-decoration-none p-1'
    tag_contents = [tag for tag in get_tags(html_group, 'a', class_=tag_class)
                    if tag.get('href') == f'/group/{group_id}/variant/'
                                          f'{variant_id}/task/{tasks_id}']
    assert len(tag_contents) == 1


def test_task_status_html_status(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    group_title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([group_title])

    variant_id = unique_int()
    db.variants.create_by_ids([variant_id])

    tasks_id = unique_int()
    db.tasks.create_by_ids([tasks_id])

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    db.statuses.submit_task(tasks_id, variant_id, group_id, unique_str(), unique_str())

    c = 'd-block text-center text-decoration-none p-1'
    for ok, text, color in [
        (False, 'x', 'background-color:#ffe3ee'),
        (True, '+', 'background-color:#e3ffee'),
        (False, '+', 'background-color:#e3ffee'),
        (True, '+', 'background-color:#e3ffee'),
    ]:
        db.statuses.check(tasks_id, variant_id, group_id, unique_str(), ok, unique_str(), unique_str())
        response = client.get(f'/group/{group_id}')
        html_group = response.get_data(as_text=True)

        url = f'/group/{group_id}/variant/{variant_id}/task/{tasks_id}'
        tags = get_tags(html_group, 'a', class_=c)
        tag_contents = next(tag for tag in tags if tag.get('href') == url)

        assert text in tag_contents.get_text()
        assert tag_contents.get('style') == color
