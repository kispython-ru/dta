from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from tests.utils import unique_str

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_group_html_prefixes(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    db.groups.create_by_names([f'{prefix}-{unique_str()}'])

    response = client.get("/")
    html = response.get_data(as_text=True)
    tag_contents = [tag.contents[0] for tag in get_tags(html, 'span')]

    assert response.content_type == 'text/html; charset=utf-8'
    assert tag_contents.count(prefix) == 1


def get_tags(html: str, pattern: str) -> ResultSet[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(pattern)
