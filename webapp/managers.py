import csv
import io
import json
import os
import random
from itertools import groupby
from typing import Callable

import bcrypt

from webapp.dto import (
    AppConfig,
    ExternalTaskDto,
    GroupDto,
    GroupInRatingDto,
    StudentInRatingDto,
    SubmissionDto,
    TaskDto,
    TaskStatusDto,
    VariantDto
)
from webapp.models import (
    FinalSeed,
    Group,
    Message,
    MessageCheck,
    Status,
    Student,
    Task,
    TaskStatus,
    TypeOfTask,
    Variant
)
from webapp.repositories import (
    FinalSeedRepository,
    GroupRepository,
    MailerRepository,
    MessageCheckRepository,
    MessageRepository,
    StudentRepository,
    TaskRepository,
    TaskStatusRepository,
    VariantRepository
)
from webapp.utils import ttl_cache


class AppConfigManager:
    def __init__(self, get_config: Callable[[], dict]):
        self.get_config = get_config

    @property
    def config(self) -> AppConfig:
        configuration = self.get_config()
        typed = AppConfig(configuration)
        return typed


class ExternalTaskManager:
    def __init__(self, groups: GroupRepository, tasks: TaskRepository):
        self.groups = groups
        self.tasks = tasks
        self.exam = None
        self.all_groups = None

    def is_exam_active(self):
        if self.exam is None:
            self.exam = any(task.type == TypeOfTask.Random for task in self.tasks.get_all())
        return self.exam

    def get_external_task(self, group: Group, variant: Variant, task: Task, seed: FinalSeed | None, config: AppConfig):
        match task.type:
            case TypeOfTask.Static:
                return ExternalTaskDto(group.id, group.external or group.title, task.id, variant.id, True)
            case TypeOfTask.Random if seed:
                h = f'{seed.seed}{task.id}{variant.id}'
                if self.all_groups is None:
                    self.all_groups = self.groups.get_all()
                group: Group = self.rnd(h, self.all_groups)
                task = self.rnd(h, config.final_tasks[str(task.id)])
                variant = self.rnd(h, list(range(1, config.final_variants + 1)))
                return ExternalTaskDto(group.id, group.external or group.title, task, variant, seed.active)
            case _:
                return ExternalTaskDto(group.id, group.external or group.title, task.id, variant.id, False)

    def rnd(self, seed: str, options: list):
        return random.Random(seed).choice(options)


class GroupManager:
    def __init__(self, groups: GroupRepository, seeds: FinalSeedRepository, external: ExternalTaskManager):
        self.seeds = seeds
        self.groups = groups
        self.external = external

    def get_groupings(self) -> dict[str, list[Group]]:
        groups = self.groups.get_all()
        exam = self.external.is_exam_active()
        groupings: dict[str, list[Group]] = {}
        for group in groups:
            if exam:
                seed = self.seeds.get_final_seed(group.id)
                if seed is None:
                    continue
                if not seed.active:
                    continue
            title: str = group.title
            key = title.split("-")[0]
            groupings.setdefault(key, []).append(group)
        return groupings


class AchievementManager:
    def __init__(self, config: AppConfigManager):
        self.achievements = None
        self.config = config

    def read_achievements(self) -> dict[str, list[int]]:
        if self.achievements is not None:
            return self.achievements
        analytics = self.config.config.analytics_path
        spec = os.path.join(analytics, 'specification.json')
        if not os.path.exists(spec):
            self.achievements = dict()
            return self.achievements
        with open(spec, 'r') as file:
            content = file.read()
            spec = json.loads(content)
            self.achievements = spec
        return self.achievements


class RatingManager:
    def __init__(
        self,
        config: AppConfigManager,
        statuses: TaskStatusRepository,
        achievements: AchievementManager,
        tasks: TaskRepository,
    ):
        self.config = config
        self.statuses = statuses
        self.achievements = achievements
        self.tasks = tasks

    @ttl_cache(duration=15, maxsize=1)
    def get_group_rating(self) -> dict[int, list[GroupInRatingDto]]:
        def key(info: tuple[Group, int]):
            group, _ = info
            return group.id

        config = self.config.config.groups
        rating = self.statuses.get_group_rating()
        places: dict[int, list[GroupInRatingDto]] = dict()
        for _, pairs in groupby(sorted(rating, key=key), key):
            pairs = list(pairs)
            group, _ = pairs[0]
            earned = sum(1 for group, var in pairs if var is not None and var < config.get(group.title, 40))
            places.setdefault(earned, [])
            places[earned].append(GroupInRatingDto(group, earned))
        return dict(sorted(places.items(), reverse=True))

    @ttl_cache(duration=15, maxsize=1)
    def get_rating(self) -> dict[int, list[StudentInRatingDto]]:
        def key(info: tuple[Group, TaskStatus]):
            _, status = info
            return status.group, status.variant

        achievements = self.achievements.read_achievements()
        statuses = self.statuses.get_rating()
        tasks = self.tasks.get_all()
        places: dict[int, list[StudentInRatingDto]] = dict()
        for _, pairs in groupby(sorted(statuses, key=key), key):
            pairs = list(pairs)
            group, status = pairs[0]
            tids = [status.task for _, status in pairs]
            if any(task.id not in tids for task in tasks):
                continue
            active = sum(len(status.achievements or [0]) for _, status in pairs if str(status.task) in achievements)
            inactive = sum(1 for _, status in pairs if str(status.task) not in achievements)
            earned = active + inactive
            places.setdefault(earned, [])
            places[earned].append(StudentInRatingDto(group, status.variant, earned))
        ordered = sorted(places.items(), reverse=True)
        return dict(ordered[0:self.config.config.places_in_rating])


class StatusManager:
    def __init__(
        self,
        tasks: TaskRepository,
        groups: GroupRepository,
        variants: VariantRepository,
        statuses: TaskStatusRepository,
        config: AppConfigManager,
        seeds: FinalSeedRepository,
        checks: MessageCheckRepository,
        achievements: AchievementManager,
        external: ExternalTaskManager,
    ):
        self.tasks = tasks
        self.groups = groups
        self.variants = variants
        self.statuses = statuses
        self.config = config
        self.seeds = seeds
        self.checks = checks
        self.achievements = achievements
        self.external = external

    def get_group_statuses(self, group_id: int, hide_pending: bool) -> GroupDto:
        config = self.config.config
        group = self.groups.get_by_id(group_id)
        seed = self.seeds.get_final_seed(group.id)
        variants = self.variants.get_all()
        tasks = self.tasks.get_all()
        statuses = self.__get_statuses(group.id)
        dtos: list[VariantDto] = []
        for var in variants:
            dto = self.__get_variant(group, var, tasks, statuses, seed, config)
            if hide_pending and all(status.status == Status.NotSubmitted for status in dto.statuses):
                continue
            dtos.append(dto)
        return GroupDto(group, [TaskDto(task, seed) for task in tasks], dtos)

    def __get_statuses(self, group: int) -> dict[tuple[int, int], TaskStatus]:
        statuses = self.statuses.get_by_group(group=group)
        return {(status.variant, status.task): status for status in statuses}

    def __get_variant(
        self,
        group: Group,
        variant: Variant,
        tasks: list[Task],
        statuses: dict[tuple[int, int], TaskStatus],
        seed: FinalSeed | None,
        config: AppConfig,
    ) -> VariantDto:
        dtos: list[TaskStatusDto] = []
        for task in tasks:
            status = statuses.get((variant.id, task.id))
            e = self.external.get_external_task(group, variant, task, seed, config)
            achievements = self.__get_task_achievements(task.id)
            dtos.append(TaskStatusDto(group, variant, TaskDto(task, seed), status, e, config, achievements))
        return VariantDto(variant, dtos)

    def __get_task_achievements(self, task: int) -> list[int]:
        achievements = self.achievements.read_achievements()
        stid = str(task)
        achievements = achievements[stid] if stid in achievements else []
        return achievements

    def get_variant_statuses(self, gid: int, vid: int) -> VariantDto:
        config = self.config.config
        variant = self.variants.get_by_id(vid)
        group = self.groups.get_by_id(gid)
        seed = self.seeds.get_final_seed(group.id)
        statuses = self.__get_statuses(group.id)
        tasks = self.tasks.get_all()
        return self.__get_variant(group, variant, tasks, statuses, seed, config)

    def get_task_status(self, gid: int, vid: int, tid: int) -> TaskStatusDto:
        status = self.statuses.get_task_status(tid, vid, gid)
        achievements = self.__get_task_achievements(tid)
        return self.__get_task_status_dto(gid, vid, tid, status, achievements)

    def __get_task_status_dto(
        self,
        gid: int, vid: int, tid: int,
        status: TaskStatus | None,
        achievements: list[int]
    ) -> TaskStatusDto:
        config = self.config.config
        group = self.groups.get_by_id(gid)
        variant = self.variants.get_by_id(vid)
        task = self.tasks.get_by_id(tid)
        seed = self.seeds.get_final_seed(gid)
        ext = self.external.get_external_task(group, variant, task, seed, self.config.config)
        return TaskStatusDto(group, variant, TaskDto(task, seed), status, ext, config, achievements)

    def get_submissions_statuses_by_info(self, gid: int, vid: int, tid: int, skip: int, take: int):
        checks = self.checks.get_by_task(gid, vid, tid, skip, take, self.config.config.enable_registration)
        return [self.__get_submissions(check, message, student) for check, message, student in checks]

    def count_submissions_by_info(self, group: int, variant: int, task: int) -> int:
        return self.checks.count_submissions_by_info(group, variant, task, self.config.config.enable_registration)

    def get_submissions_statuses(self, student: Student, skip: int, take: int) -> list[SubmissionDto]:
        checks = self.checks.get_by_student(student, skip, take)
        return [self.__get_submissions(check, message, None) for check, message in checks]

    def get_anonymous_submissions_statuses(self, session_id: str, skip: int, take: int) -> list[SubmissionDto]:
        checks = self.checks.get_by_session_id(session_id, skip, take)
        return [self.__get_submissions(check, message, None) for check, message in checks]

    def __get_submissions(self, check: MessageCheck, message: Message, student: Student | None):
        return SubmissionDto(self.__get_task_status_dto(message.group, message.variant, message.task, TaskStatus(
            task=message.task,
            variant=message.variant,
            group=message.group,
            time=check.time,
            code=message.code,
            ip=message.ip,
            output=check.output,
            status=check.status,
            achievements=[]
        ), []), message.code, check.time, message.time, message.ip, student)


class HomeManager:
    def __init__(self, rating: RatingManager):
        self.rating = rating

    def get_group_place(self, gid: int) -> int:
        groupings = self.rating.get_group_rating()
        for place, groups in enumerate(groupings.values()):
            for group in groups:
                if group.group.id == gid:
                    return place

    def get_student_place(self, gid: int, vid: int) -> int:
        students = self.rating.get_rating()
        for place, students in enumerate(students.values()):
            for student in students:
                if student.group.id == gid and student.variant == vid:
                    return place


class StudentManager:
    def __init__(self, config: AppConfigManager, students: StudentRepository, mailers: MailerRepository):
        self.students = students
        self.mailers = mailers
        self.config = config

    def hide_email(self, value: str):
        if '@' not in value:
            return value
        username, domain = value.split('@')
        length = len(username)
        if length == 1:
            return f'*@{domain}'
        repeat = min((length - 1), 10) * '*'
        return f'{username[0]}{repeat}@{domain}'

    def register(self, email: str, password: str) -> str:
        if self.exists(email):
            if self.blocked(email):
                return "Данный адрес электронной почты заблокирован."
            if self.confirmed(email):
                return "Такой адрес почты уже зарегистрирован! Нажмите кнопку 'Войти'."
            student = self.students.find_by_email(email)
            if student and student.provider:
                return "Воспользуйтесь кнопкой 'Сменить пароль', если хотите выполнить вход по паролю."
            return (f"Пользователь не подтверждён! Отправьте пустое сообщение с Вашего адреса "
                    f"электронной почты {email} на наш адрес {self.config.config.imap_login} "
                    "для подтверждения. В течение 5 минут после отправки письма Ваш аккаунт "
                    "будет активирован.")
        if not self.email_allowed(email):
            domains = self.mailers.get_domains()
            desc = ", ".join(domains).rstrip().rstrip(',')
            return (f'Данный поставщик услуг электронной почты не поддерживается. '
                    f'Поддерживаемые поставщики: {desc}.')
        self.create(email, password)
        return (f"Вы успешно зарегистрировались, однако Ваш адрес электронной почты не подтверждён. "
                f"Отправьте пустое сообщение с Вашего адреса электронной почты {email} на "
                f"наш адрес {self.config.config.imap_login} для подтверждения. В течение 5 минут "
                "после отправки письма Ваш аккаунт будет активирован.")

    def change_password(self, email: str, new_password: str) -> str:
        if not self.exists(email):
            return "Такой адрес почты не зарегистрирован!"
        if self.blocked(email):
            return "Данный адрес электронной почты заблокирован."
        student = self.students.find_by_email(email)
        if not self.confirmed(email) and not student.provider:
            return (f"Пользователь не подтверждён! Отправьте пустое сообщение с Вашего адреса "
                    f"электронной почты {email} на наш адрес {self.config.config.imap_login} "
                    "для подтверждения. В течение 5 минут после отправки письма Ваш аккаунт "
                    "будет активирован.")
        if not self.update_password(email, new_password):
            return f"Изменение пароля невозможно, обратитесь к администратору."
        return (f"Запрос на изменение пароля создан! Отправьте пустое сообщение с Вашего адреса "
                f"электронной почты {email} на наш адрес {self.config.config.imap_login} "
                "для подтверждения операции изменения пароля. В течение 5 минут после отправки "
                "письма Вы сможете использовать новый пароль для входа на сайт.")

    def login(self, email: str, password: str) -> str | None:
        if not self.exists(email):
            return "Такой адрес почты не зарегистрирован!"
        if self.blocked(email):
            return "Данный адрес электронной почты заблокирован."
        if not self.confirmed(email):
            student = self.students.find_by_email(email)
            if student and student.provider:
                return "Воспользуйтесь кнопкой 'Сменить пароль', если хотите выполнить вход по паролю."
            return (f"Пользователь не подтверждён! Отправьте пустое сообщение с Вашего адреса "
                    f"электронной почты {email} на наш адрес {self.config.config.imap_login} "
                    "для подтверждения Вашего аккаунта. В течение 5 минут после отправки "
                    "письма Вы сможете использовать новый пароль для входа на сайт.")
        if not self.check_password(email, password):
            return "Неправильный пароль."
        return None

    def check_password(self, email: str, password: str) -> Student | None:
        student = self.students.find_by_email(email)
        if student and student.password_hash:
            given = password.encode('utf8')
            actual = student.password_hash.encode('utf8')
            if bcrypt.checkpw(given, actual):
                return student

    def update_password(self, email: str, password: str) -> bool:
        student = self.students.find_by_email(email)
        if student and (student.password_hash or student.provider):
            given = password.encode('utf8')
            hashed = bcrypt.hashpw(given, bcrypt.gensalt())
            self.students.change_password(email, hashed.decode('utf8'))
            return True
        return False

    def confirmed(self, email: str) -> bool:
        student = self.students.find_by_email(email)
        return student and student.password_hash

    def blocked(self, email: str) -> bool:
        student = self.students.find_by_email(email)
        return student and student.blocked

    def exists(self, email: str) -> bool:
        student = self.students.find_by_email(email)
        return bool(student)

    def email_allowed(self, email: str) -> bool:
        _, domain = email.split('@')
        exists = self.mailers.exists(domain)
        return exists

    def create(self, email: str, password: str, teacher=False) -> int:
        given = password.encode('utf8')
        hashed = bcrypt.hashpw(given, bcrypt.gensalt())
        student = self.students.create(email, hashed.decode('utf8'), teacher)
        return student.id


class ExportManager:
    def __init__(
        self,
        groups: GroupRepository,
        messages: MessageRepository,
        statuses: StatusManager,
        variants: VariantRepository,
        tasks: TaskRepository,
        students: StudentRepository,
        manager: StudentManager,
    ):
        self.groups = groups
        self.messages = messages
        self.statuses = statuses
        self.variants = variants
        self.tasks = tasks
        self.students = students
        self.manager = manager

    def export_messages(self, count: int | None, separator: str) -> str:
        messages = self.__get_latest_messages(count)
        group_titles = self.__get_group_titles()
        table = self.__create_messages_table(messages, group_titles)
        delimiter = ";" if separator == ";" else ","
        output = self.__create_csv(table, delimiter)
        return output

    def export_exam_results(self, group_id: int, separator: str) -> str:
        table = self.__create_exam_table(group_id)
        delimiter = ";" if separator == "semicolon" else ","
        output = self.__create_csv(table, delimiter)
        return output

    def __create_messages_table(self, messages: list[Message], group_titles: dict[int, str]) -> list[list[str]]:
        rows = [["ID", "Время", "Группа", "Задача", "Вариант", "IP", "Отправитель", "Код"]]
        for message in messages:
            gt = group_titles[message.group]
            time = message.time.strftime("%Y-%m-%d %H:%M:%S")
            task = message.task + 1
            variant = message.variant + 1
            code = message.code
            ip = message.ip
            id = message.id
            sid = message.student
            email = self.manager.hide_email(self.students.get_by_id(sid).email) if sid else None
            rows.append([id, time, gt, task, variant, ip, email, code])
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
