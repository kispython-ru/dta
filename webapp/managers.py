import csv
import io
from typing import Dict, List, Union

from webapp.models import Message, TaskStatus, TaskStatusEnum
from webapp.repositories import GroupRepository, MessageRepository


def find_task_status(
    statuses: List[TaskStatus],
    group_id: int,
    variant_id: int,
    task_id: int
) -> TaskStatusEnum:
    for status in statuses:
        if status.group == group_id and \
           status.variant == variant_id and \
           status.task == task_id:
            return status.status
    return TaskStatusEnum.NotSubmitted


class ExportManager:
    def __init__(self, groups: GroupRepository, messages: MessageRepository):
        self.groups = groups
        self.messages = messages

    def export_messages(self, count: Union[int, None], separator: str) -> str:
        messages = self.get_latest_messages(count)
        group_titles = self.get_group_titles()
        table = self.create_table(messages, group_titles)
        delimiter = ";" if separator == "semicolon" else ","
        output = self.create_csv(table, delimiter)
        return output

    def create_csv(self, table: List[List[str]], delimiter: str):
        si = io.StringIO()
        cw = csv.writer(si, delimiter=delimiter)
        cw.writerows(table)
        bom = u"\uFEFF"
        value = bom + si.getvalue()
        return value

    def create_table(
        self,
        messages: List[Message],
        group_titles: Dict[int, str]
    ) -> List[List[str]]:
        rows = [["ID", "Время", "Группа", "Задача", "Вариант", "IP", "Код"]]
        for message in messages:
            group_title = group_titles[message.group]
            time = message.time.strftime("%Y-%m-%d %H:%M:%S")
            task = message.task + 1
            variant = message.variant + 1
            rows.append([
                message.id,
                time,
                group_title,
                task,
                variant,
                message.ip,
                message.code
            ])
        return rows

    def get_group_titles(self) -> Dict[int, str]:
        groups = self.groups.get_all()
        group_titles: Dict[int, str] = {}
        for group in groups:
            group_titles[group.id] = group.title
        return group_titles

    def get_latest_messages(self, count: Union[int, None]) -> List[Message]:
        if count is None:
            return self.messages.get_all()
        return self.messages.get_latest(count)
