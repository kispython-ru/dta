from tests.utils import get_tags, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_group_html_prefixes(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    db.groups.create_by_names([f'{prefix}-{unique_str()}'])

    response = client.get("/")
    html = response.get_data(as_text=True)
    text = [tag.get_text().strip() for tag in get_tags(html, 'small', 'text-muted')]

    assert response.content_type == 'text/html; charset=utf-8'
    assert text.count(prefix) == 1


def test_group_html_title(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([title])

    response = client.get('/')
    html = response.get_data(as_text=True)
    contents = [tag.get_text() for tag in get_tags(html, 'a', True)]

    assert response.content_type == 'text/html; charset=utf-8'
    assert len([text for text in contents if title in text]) == 1


def test_group_html_link(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([title])

    response = client.get('/')
    html_dashboard = response.get_data(as_text=True)

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tags = [tag.get('href') for tag in get_tags(html_dashboard, 'a', True)]
    tag_contents = next(tag for tag in tags if tag == f'/group/{group_id}')

    response = client.get(tag_contents)
    html_group_href = response.get_data(as_text=True)

    assert response.content_type == 'text/html; charset=utf-8'
    assert html_group_href == html_group
