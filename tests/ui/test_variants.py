from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from tests.utils import unique_str, unique_int
from typing import Union

from flask.testing import FlaskClient

from webapp.repositories import AppDatabase


def test_variant_html_id(db: AppDatabase, client: FlaskClient):
    prefix = unique_str().replace('-', '')
    group_title = f'{prefix}-{unique_str()}'
    db.groups.create_by_names([group_title])

    variant_id = unique_int()
    db.variants.create_by_ids([variant_id])

    group_id = next(group.id for group in db.groups.get_by_prefix(prefix))
    response = client.get(f'/group/{group_id}')
    html_group = response.get_data(as_text=True)

    tag_contents = [tag.get_text() for tag in get_tags(html_group, 'span', True)]

    assert tag_contents.count(f'{variant_id + 1}') == 1


def test_variant_html_link(db: AppDatabase, client: FlaskClient):
    pass


def get_tags(html: str, name: str, class_: Union[str, bool]) -> ResultSet[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(name, class_=class_)
