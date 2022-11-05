import csv
import io
import random
from typing import Callable

import bcrypt

from flask import Config

from webapp.dto import AppConfig, ExternalTaskDto, GroupDto, TaskDto, TaskStatusDto, VariantDto
from webapp.models import FinalSeed, Group, Message, Student, Task, TaskStatus, Teacher, Variant
from webapp.repositories import (
    FinalSeedRepository,
    GroupRepository,
    MailerRepository,
    MessageRepository,
    StudentRepository,
    TaskRepository,
    TaskStatusRepository,
    TeacherRepository,
    VariantRepository
)


class AppConfigManager:
    def __init__(self, get_config: Callable[[], Config]):
        self.get_config = get_config

    @property
    def config(self) -> AppConfig:
        configuration = self.get_config()
        return AppConfig(configuration)


class GroupManager:
    def __init__(
        self,
        config: AppConfigManager,
        groups: GroupRepository,
        seeds: FinalSeedRepository
    ):
        self.seeds = seeds
        self.groups = groups
        self.config = config

    def get_groupings(self) -> dict[str, list[Group]]:
        config = self.config.config
        groups = self.groups.get_all()
        groupings: dict[str, list[Group]] = {}
        for group in groups:
            if config.exam:
                seed = self.seeds.get_final_seed(group.id)
                if seed is None:
                    continue
                if not seed.active:
                    continue
            title: str = group.title
            key = title.split("-")[0]
            groupings.setdefault(key, []).append(group)
        return groupings


class ExternalTaskManager:
    def __init__(
        self,
        group: Group,
        seed: FinalSeed | None,
        tasks: TaskRepository,
        groups: GroupRepository,
        variants: VariantRepository,
        config: AppConfig,
    ):
        self.config = config
        self.group = group
        self.seed = seed
        self.tasks = tasks
        self.groups = groups
        self.variants = variants
        self.fetch_lists()

    @property
    def random_active(self) -> bool:
        return self.seed is not None and self.seed.active

    def get_external_task(self, task: int, variant: int) -> ExternalTaskDto:
        if self.seed is None:
            return ExternalTaskDto(
                group_title=self.group.title,
                task=task,
                variant=variant,
                active=True
            )
        unique = f'{task}{variant}'
        task: Task = self.sample_task(str(variant), task)
        group: Group = self.sample(unique, self.all_groups, self.group.id)
        variant: Variant = self.sample(unique, self.all_variants, variant)
        return ExternalTaskDto(
            task=task.id,
            group_title=group.title,
            variant=variant.id,
            active=bool(self.seed.active),
        )

    def sample_task(self, seed: str, task: int):
        final_tasks: dict[str, list[int]] = self.config.final_tasks
        if not final_tasks:
            return self.sample(seed, self.all_tasks, task)
        possible_options: list[int] = final_tasks[str(task)]
        composite_seed = f'{self.seed.seed}{seed}'
        rand = random.Random(composite_seed)
        id = rand.choice(possible_options)
        return Task(id=id)

    def sample(self, seed: str, list: list[dict[str, int]], i: int):
        composite_seed = f'{self.seed.seed}{seed}'
        rand = random.Random(composite_seed)
        length = len(list)
        identifiers = [item.id for item in list]
        index = identifiers.index(i)
        random_sample = rand.sample(list, length)
        return random_sample[index]

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
    ):
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
        e = self.__get_external_task_manager(group)
        tasks = self.__get_tasks(group, config, e.random_active)
        dtos: list[VariantDto] = []
        for var in variants:
            dto = self.__get_variant(group, var, tasks, statuses, config, e)
            dtos.append(dto)
        return GroupDto(group, tasks, dtos)

    def get_variant_statuses(self, gid: int, vid: int) -> VariantDto:
        config = self.config.config
        group = self.groups.get_by_id(gid)
        variant = self.variants.get_by_id(vid)
        statuses = self.__get_statuses(group.id)
        e = self.__get_external_task_manager(group)
        tasks = self.__get_tasks(group, config, e.random_active)
        dto = self.__get_variant(group, variant, tasks, statuses, config, e)
        return dto

    def get_task_status(self, gid: int, vid: int, tid: int) -> TaskStatusDto:
        config = self.config.config
        group = self.groups.get_by_id(gid)
        variant = self.variants.get_by_id(vid)
        task = self.tasks.get_by_id(tid)
        status = self.statuses.get_task_status(tid, vid, gid)
        e = self.__get_external_task_manager(group)
        ext = e.get_external_task(task.id, variant.id)
        task_dto = TaskDto(group, task, config, e.random_active)
        return TaskStatusDto(group, variant, task_dto, status, ext, config)

    def __get_external_task_manager(self, group: Group) -> ExternalTaskManager:
        seed = self.seeds.get_final_seed(group.id)
        return ExternalTaskManager(
            group=group,
            seed=seed,
            tasks=self.tasks,
            groups=self.groups,
            variants=self.variants,
            config=self.config.config,
        )

    def __get_variant(
        self,
        group: Group,
        variant: Variant,
        tasks: list[TaskDto],
        statuses: dict[tuple[int, int], TaskStatus],
        config: AppConfig,
        external: ExternalTaskManager,
    ) -> VariantDto:
        dtos: list[TaskStatusDto] = []
        for task in tasks:
            composite_key: tuple[int, int] = (variant.id, task.id)
            status = statuses.get(composite_key)
            e = external.get_external_task(task.id, variant.id)
            dto = TaskStatusDto(group, variant, task, status, e, config)
            dtos.append(dto)
        return VariantDto(variant, dtos)

    def __get_tasks(
        self,
        group: Group,
        config: AppConfig,
        active: bool
    ) -> list[TaskDto]:
        tasks = self.tasks.get_all()
        dtos: list[TaskDto] = []
        for task in tasks:
            dto = TaskDto(group, task, config, active)
            dtos.append(dto)
        return dtos

    def __get_statuses(self, group: int) -> dict[tuple[int, int], TaskStatus]:
        statuses = self.statuses.get_by_group(group=group)
        dictionary = dict()
        for status in statuses:
            composite_key: tuple[int, int] = (status.variant, status.task)
            dictionary[composite_key] = status
        return dictionary


class ExportManager:
    def __init__(
        self,
        groups: GroupRepository,
        messages: MessageRepository,
        statuses: StatusManager,
        variants: VariantRepository,
        tasks: TaskRepository
    ):
        self.groups = groups
        self.messages = messages
        self.statuses = statuses
        self.variants = variants
        self.tasks = tasks

    def export_messages(self, count: int | None, separator: str) -> str:
        messages = self.__get_latest_messages(count)
        group_titles = self.__get_group_titles()
        table = self.__create_messages_table(messages, group_titles)
        delimiter = ";" if separator == "semicolon" else ","
        output = self.__create_csv(table, delimiter)
        return output

    def export_exam_results(
        self,
        group_id: int,
        separator: str
    ) -> str:
        table = self.__create_exam_table(group_id)
        delimiter = ";" if separator == "semicolon" else ","
        output = self.__create_csv(table, delimiter)
        return output

    def __create_messages_table(
        self,
        messages: list[Message],
        group_titles: dict[int, str]
    ) -> list[list[str]]:
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

    def __create_exam_table(self, group_id: int) -> list[list[str]]:
        header = ['Сдающая группа', 'Вариант']
        tasks = self.tasks.get_all()
        for task in tasks:
            id = task.id + 1
            header += [
                f'№{id} Статус',
                f'№{id} Группа',
                f'№{id} Вариант',
                f'№{id} Задача',
                f'№{id} IP адрес'
            ]
        header.append('Решено задач')
        rows = []
        for variant in self.variants.get_all():
            group_title = self.groups.get_by_id(group_id).title
            row = [group_title, variant.id + 1]
            score = 0
            for task in tasks:
                info = self.statuses.get_task_status(
                    group_id,
                    variant.id,
                    task.id
                )
                status = 1 if info.status.value == 2 else 0
                row.append(status)
                row.append(info.external.group_title)
                row.append(info.external.variant + 1)
                row.append(info.external.task + 1)
                row.append(info.ip)
                score += status
            row.append(score)
            rows.append(row)
        return [header] + rows

    def __get_group_titles(self) -> dict[int, str]:
        groups = self.groups.get_all()
        group_titles: dict[int, str] = {}
        for group in groups:
            group_titles[group.id] = group.title
        return group_titles

    def __get_latest_messages(self, count: int | None) -> list[Message]:
        if count is None:
            return self.messages.get_all()
        return self.messages.get_latest(count)

    def __create_csv(self, table: list[list[str]], delimiter: str):
        si = io.StringIO()
        cw = csv.writer(si, delimiter=delimiter)
        cw.writerows(table)
        bom = u"\uFEFF"
        value = bom + si.getvalue()
        return value


class TeacherManager:
    def __init__(self, teachers: TeacherRepository):
        self.teachers = teachers

    def check_password(self, login: str, password: str) -> Teacher | None:
        teacher = self.teachers.find_by_login(login)
        if teacher is not None:
            given = password.encode('utf8')
            actual = teacher.password_hash.encode('utf8')
            if bcrypt.checkpw(given, actual):
                return teacher


class StudentManager:
    def __init__(self, students: StudentRepository, mailers: MailerRepository):
        self.students = students
        self.mailers = mailers

    def check_password(self, email: str, password: str) -> Student | None:
        student = self.students.find_by_email(email)
        if student is not None and student.password_hash is not None:
            given = password.encode('utf8')
            actual = student.password_hash.encode('utf8')
            if bcrypt.checkpw(given, actual):
                return student

    def change_password(self, email: str, password: str) -> bool:
        student = self.students.find_by_email(email)
        if student is not None and student.password_hash is not None:
            given = password.encode('utf8')
            hashed = bcrypt.hashpw(given, bcrypt.gensalt())
            self.students.change_password(email, hashed.decode('utf8'))
            return True
        return False

    def confirmed(self, email: str) -> bool:
        student = self.students.find_by_email(email)
        return student is not None and student.password_hash is not None

    def exists(self, email: str) -> bool:
        student = self.students.find_by_email(email)
        return bool(student)

    def email_allowed(self, email: str) -> bool:
        _, domain = email.split('@')
        exists = self.mailers.exists(domain)
        return exists

    def create(self, email: str, password: str) -> int:
        given = password.encode('utf8')
        hashed = bcrypt.hashpw(given, bcrypt.gensalt())
        student = self.students.create(email, hashed.decode('utf8'))
        return student.id
