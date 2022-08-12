import datetime
import time
import uuid

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from webapp.repositories import AppDatabase


def unique_str() -> str:
    unique_id = uuid.uuid4()
    return str(unique_id)


def unique_int() -> int:
    unique_id = uuid.uuid4().node
    return int(unique_id)


def timeout_assert(condition: callable[[], bool], timeout: int = 20):
    delta = datetime.timedelta(seconds=timeout)
    started = datetime.datetime.now()
    while True:
        time.sleep(1)
        if datetime.datetime.now() > started + delta:
            raise Exception("Time is out, assertion failed.")
        if condition():
            break


def arrange_task(db: AppDatabase) -> tuple[int, int, int]:
    variant = unique_int()
    group_name = unique_str()
    task = unique_int()

    db.variants.create_by_ids([variant])
    db.groups.create(group_name)
    db.tasks.create_by_ids([task])

    group = db.groups.get_by_prefix(group_name)[0].id
    return (group, variant, task)


def get_tags(
    html: str,
    name: str,
    class_: str | bool | None,
) -> ResultSet[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(name, class_=class_)
