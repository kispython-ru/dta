import csv
import io
import random
from typing import Callable, Dict, List, Tuple, Union

from flask import Config

from webapp.dto import (
    AppConfig,
    ExternalTaskDto,
    GroupDto,
    TaskDto,
    TaskStatusDto,
    VariantDto
)
from webapp.models import FinalSeed, Group, Message, TaskStatus, Variant
from webapp.repositories import (
    FinalSeedRepository,
    GroupRepository,
    MessageRepository,
    TaskRepository,
    TaskStatusRepository,
    VariantRepository
)


class AppConfigManager:
    def __init__(self, get_config: Callable[[], Config]):
        self.get_config = get_config

    @property
    def config(self) -> AppConfig:
        configuration = self.get_config()
        return AppConfig(configuration)


class ExternalTaskManager:
    def __init__(
        self,
        group: Group,
        seed: Union[FinalSeed, None],
        tasks: TaskRepository,
        groups: GroupRepository,
        variants: VariantRepository,
    ) -> None:
        self.group = group
        self.seed = seed
        self.tasks = tasks
        self.groups = groups
        self.variants = variants
        self.fetch_lists()

    def get_external_task(self, task: int, variant: int) -> ExternalTaskDto:
        if self.seed is None:
            return ExternalTaskDto(self.group.title, task, variant)
        composite_seed = f'{self.seed.seed}{task}{variant}'
        rand = random.Random(composite_seed)
        return ExternalTaskDto(
            group_title=rand.choice(self.all_groups).title,
            task=rand.choice(self.all_tasks),
            variant=rand.choice(self.all_variants)
        )

    def fetch_lists(self):
        if self.seed is None:
            return
        self.all_tasks = self.tasks.get_all()
        self.all_variants = self.variants.get_all()
        self.all_groups = self.groups.get_all()


class StatusManager:
    def __init__(
        self,
        tasks: TaskRepository,
        groups: GroupRepository,
        variants: VariantRepository,
        statuses: TaskStatusRepository,
        config: AppConfigManager,
        seeds: FinalSeedRepository,
    ) -> None:
        self.tasks = tasks
        self.groups = groups
        self.variants = variants
        self.statuses = statuses
        self.config = config
        self.seeds = seeds

    def get_group_statuses(self, group_id: int) -> GroupDto:
        config = self.config.config
        group = self.groups.get_by_id(group_id)
        variants = self.variants.get_all()
        statuses = self.__get_statuses(group.id)
        tasks = self.__get_tasks(group, config)
        e = self.__get_external_task_manager(group)
        dtos: List[VariantDto] = []
        for var in variants:
            dto = self.__get_variant(group, var, tasks, statuses, config, e)
            dtos.append(dto)
        return GroupDto(group, tasks, dtos)

    def get_variant_statuses(self, gid: int, vid: int) -> VariantDto:
        config = self.config.config
        group = self.groups.get_by_id(gid)
        variant = self.variants.get_by_id(vid)
        statuses = self.__get_statuses(group.id)
        tasks = self.__get_tasks(group, config)
        e = self.__get_external_task_manager(group)
        dto = self.__get_variant(group, variant, tasks, statuses, config, e)
        return dto

    def get_task_status(self, gid: int, vid: int, tid: int) -> TaskStatusDto:
        base_url = self.config.config.task_base_url
        group = self.groups.get_by_id(gid)
        variant = self.variants.get_by_id(vid)
        task = self.tasks.get_by_id(tid)
        status = self.statuses.get_task_status(tid, vid, gid)
        task_dto = TaskDto(group, task, base_url)
        external = self.__get_external_task_manager(group)
        e = external.get_external_task(task.id, variant.id)
        return TaskStatusDto(group, variant, task_dto, status, e, base_url)

    def __get_external_task_manager(self, group: Group) -> ExternalTaskManager:
        seed = self.seeds.get_final_seed(group.id)
        return ExternalTaskManager(
            group=group,
            seed=seed,
            tasks=self.tasks,
            groups=self.groups,
            variants=self.variants
        )

    def __get_variant(
        self,
        group: Group,
        variant: Variant,
        tasks: List[TaskDto],
        statuses: Dict[Tuple[int, int], TaskStatus],
        config: AppConfig,
        external: ExternalTaskManager,
    ) -> VariantDto:
        base_url = config.task_base_url
        dtos: List[TaskStatusDto] = []
        for task in tasks:
            composite_key: Tuple[int, int] = (variant.id, task.id)
            status = statuses.get(composite_key)
            e = external.get_external_task(task.id, variant.id)
            dto = TaskStatusDto(group, variant, task, status, e, base_url)
            dtos.append(dto)
        return VariantDto(variant, dtos)

    def __get_tasks(self, group: Group, config: AppConfig) -> List[TaskDto]:
        base_url = config.task_base_url
        tasks = self.tasks.get_all()
        dtos: List[TaskDto] = []
        for task in tasks:
            dto = TaskDto(group, task, base_url)
            dtos.append(dto)
        return dtos

    def __get_statuses(self, group: int) -> Dict[Tuple[int, int], TaskStatus]:
        statuses = self.statuses.get_by_group(group=group)
        dictionary = dict()
        for status in statuses:
            composite_key: Tuple[int, int] = (status.variant, status.task)
            dictionary[composite_key] = status
        return dictionary


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
            gt = group_titles[message.group]
            time = message.time.strftime("%Y-%m-%d %H:%M:%S")
            task = message.task + 1
            variant = message.variant + 1
            code = message.code
            ip = message.ip
            id = message.id
            rows.append([id, time, gt, task, variant, ip, code])
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
