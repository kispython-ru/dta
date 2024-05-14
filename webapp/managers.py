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
from webapp.models import FinalSeed, Group, Message, MessageCheck, Student, Task, TaskStatus, Variant
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


class AppConfigManager:
    def __init__(self, get_config: Callable[[], dict]):
        self.get_config = get_config

    @property
    def config(self) -> AppConfig:
        configuration = self.get_config()
        typed = AppConfig(configuration)
        return typed


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
        return self.seed and self.seed.active

    def get_external_task(self, task: int, variant: int) -> ExternalTaskDto:
        if self.seed is None:
            not_exam_mode = not self.config.final_tasks
            return ExternalTaskDto(
                group_title=self.group.title,
                task=task,
                variant=variant,
                active=not_exam_mode
            )
        unique = f'{task}{variant}'
        task: Task = self.sample_task(str(variant), task)
        group: Group = self.sample(unique, self.all_groups, self.group.id)
        variant: Variant = self.sample(unique, self.all_variants, variant)
        return ExternalTaskDto(
            task=task.id,
            group_title=group.external if group.external else group.title,
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
        checks: MessageCheckRepository
    ):
        self.tasks = tasks
        self.groups = groups
        self.variants = variants
        self.statuses = statuses
        self.config = config
        self.seeds = seeds
        self.checks = checks
        self.achievements = None

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

    def get_rating(self) -> dict[int, list[StudentInRatingDto]]:
        def key(info: tuple[Group, TaskStatus]):
            _, status = info
            return status.group, status.variant

        achievements = self.__read_achievements()
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
        status = self.statuses.get_task_status(tid, vid, gid)
        achievements = self.__get_task_achievements(tid)
        return self.__get_task_status_dto(gid, vid, tid, status, achievements)

    def get_submissions_statuses_by_info(
        self,
        group: int,
        variant: int,
        task: int,
        skip: int,
        take: int,
    ) -> list[SubmissionDto]:
        registration = self.config.config.enable_registration
        submissions = []
        checks = self.checks.get_by_task(group, variant, task, skip, take, registration)
        for check, message, student in checks:
            submissions.append(self.__get_submissions(check, message, student))
        return submissions

    def count_submissions_by_info(self, group: int, variant: int, task: int) -> int:
        registration = self.config.config.enable_registration
        return self.checks.count_submissions_by_info(group, variant, task, registration)

    def get_submissions_statuses(self, student: Student, skip: int, take: int) -> list[SubmissionDto]:
        checks_and_messages: list[tuple[MessageCheck, Message]] = self.checks.get_by_student(student, skip, take)
        submissions = []
        for check, message in checks_and_messages:
            submissions.append(self.__get_submissions(check, message, None))
        return submissions

    def get_anonymous_submissions_statuses(self, session_id: str, skip: int, take: int) -> list[SubmissionDto]:
        checks_and_messages: list[tuple[MessageCheck, Message]] = self.checks.get_by_session_id(session_id, skip, take)
        submissions = []
        for check, message in checks_and_messages:
            submissions.append(self.__get_submissions(check, message, None))
        return submissions

    def count_student_submissions(self, student: Student) -> int:
        return self.checks.count_student_submissions(student)

    def count_session_id_submissions(self, session_id: str) -> int:
        return self.checks.count_session_id_submissions(session_id)

    def __get_submissions(
        self,
        check: MessageCheck,
        message: Message,
        student: Student | None
    ):
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
        ), []), message.code, check.time, message.time, student)

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
        e = self.__get_external_task_manager(group)
        ext = e.get_external_task(task.id, variant.id)
        task_dto = TaskDto(group, task, config, e.random_active)
        return TaskStatusDto(group, variant, task_dto, status, ext, config, achievements)

    def __get_task_achievements(self, task: int) -> list[int]:
        achievements = self.__read_achievements()
        stid = str(task)
        achievements = achievements[stid] if stid in achievements else []
        return achievements

    def __read_achievements(self) -> dict[str, list[int]]:
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
            achievements = self.__get_task_achievements(task.id)
            dto = TaskStatusDto(group, variant, task, status, e, config, achievements)
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
