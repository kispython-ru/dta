from tests.utils import get_tags, unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_group_html_prefixes(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    db.groups.create_by_names([f'{prefix}-{unique_str()}'])

    response = client.get("/")
    html = response.get_data(as_text=True)
    tag_contents = [tag.contents[0] for tag in get_tags(html, 'span', None)]

    assert response.content_type == 'text/html; charset=utf-8'
    assert tag_contents.count(prefix) == 1


def test_group_html_title(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([title])

    response = client.get('/')
    html = response.get_data(as_text=True)

    tag_contents = [tag.get_text() for tag in get_tags(html, 'a', True)]
    number = [tag_content for tag_content in tag_contents if title in tag_content]

    assert response.content_type == 'text/html; charset=utf-8'
    assert len(number) == 1


def test_group_html_link(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([title])

    response = client.get('/')
    html_dashboard = response.get_data(as_text=True)

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tag_contents = next(tag.get('href') for tag in get_tags(html_dashboard, 'a', True) if
                        tag.get('href') == f'/group/{group_id}')

    response = client.get(tag_contents)
    html_group_href = response.get_data(as_text=True)

    assert response.content_type == 'text/html; charset=utf-8'
    assert html_group_href == html_group
