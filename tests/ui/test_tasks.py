from tests.utils import get_tags, unique_int, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_task_html_id(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([title])

    task_id = unique_int()
    db.tasks.create(task_id)

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tag_contents = [tag for tag in
                    get_tags(html_group, 'td', True)
                    if f'№{task_id + 1}' in tag.get_text()]

    assert len(tag_contents) == 1
