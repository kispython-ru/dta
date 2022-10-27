from flask import Config

from webapp.models import Group, Status, Task, TaskStatus, Variant


class AppConfig:
    def __init__(self, config: Config):
        self.highlight_syntax: bool = config["HIGHLIGHT_SYNTAX"]
        self.core_path: str = config["CORE_PATH"]
        self.analytics_path: str = config["ANALYTICS_PATH"]
        self.api_token: str = config["API_TOKEN"]
        self.connection_string: str = config["CONNECTION_STRING"]
        self.task_base_url: str = config["TASK_BASE_URL"]
        self.no_background_worker: bool = config["DISABLE_BACKGROUND_WORKER"]
        self.final_tasks: dict[str, list[int]] = config["FINAL_TASKS"]
        self.readonly: bool = config["READONLY"]
        self.enable_registration: bool = config["ENABLE_REGISTRATION"]
        self.imap_login: bool = config["IMAP_LOGIN"]
        self.imap_password: bool = config["IMAP_PASSWORD"]


class ExternalTaskDto:
    def __init__(
        self,
        group_title: str,
        task: int,
        variant: int,
        active: bool
    ):
        self.group_title = group_title
        self.task = task
        self.variant = variant
        self.active = active


class TaskDto:
    def __init__(
        self,
        group: Group,
        task: Task,
        config: AppConfig,
        random: bool
    ):
        self.id = int(task.id)
        self.original = f'{config.task_base_url}/{self.id}/{group.title}.html'
        self.url = self.original if not random else "#"
        self.formulation = task.formulation


class TaskStatusDto:
    def __init__(
        self,
        group: Group,
        variant: Variant,
        task: TaskDto,
        status: TaskStatus | None,
        external: ExternalTaskDto,
        config: AppConfig,
    ):
        self.task = task.id
        self.formulation = task.formulation
        self.ip = status.ip if status is not None else "-"
        self.variant = variant.id
        self.group = int(group.id)
        self.group_title = group.title
        self.base_url = config.task_base_url
        self.external = external
        self.status = Status.NotSubmitted if status is None else status.status
        self.checked = self.status == Status.Checked
        self.error_message = status.output if self.status == Status.Failed else None
        self.analytics = status.output if self.status == Status.Checked else None
        self.readonly = config.readonly

    @property
    def submission_url(self) -> str:
        gid = self.group
        vid = self.variant
        tid = self.task
        return f'/group/{gid}/variant/{vid}/task/{tid}'

    @property
    def formulation_url(self) -> str:
        git = self.external.group_title
        vid = self.external.variant
        tid = self.external.task
        furl = self.base_url
        return f'{furl}/{tid}/{git}.html#вариант-{vid + 1}'

    @property
    def cell_background(self) -> str:
        return self.map_status({
            Status.Submitted: "inherit",
            Status.Checking: "inherit",
            Status.Checked: "#e3ffee",
            Status.Failed: "#ffe3ee",
            Status.NotSubmitted: "inherit",
        })

    @property
    def name(self) -> str:
        return self.map_status({
            Status.Submitted: "Отправлено",
            Status.Checking: "Проверяется",
            Status.Checked: "Принято",
            Status.Failed: "Ошибка!",
            Status.NotSubmitted: "Не отправлено",
        })

    @property
    def code(self) -> str:
        return self.map_status({
            Status.Submitted: "?",
            Status.Checking: "...",
            Status.Checked: "+",
            Status.Failed: "x",
            Status.NotSubmitted: "-",
        })

    @property
    def color(self) -> str:
        return self.map_status({
            Status.Submitted: "primary",
            Status.Checking: "warning",
            Status.Checked: "success",
            Status.Failed: "danger",
            Status.NotSubmitted: "secondary",
        })

    @property
    def disabled(self) -> bool:
        checked = self.status == Status.Checked
        active = self.external.active
        return checked or not active or self.readonly

    def map_status(self, map: dict[Status, str]):
        return map[self.status]


class VariantDto:
    def __init__(self, variant: Variant, statuses: list[TaskStatusDto]):
        self.id = int(variant.id)
        self.statuses = statuses


class GroupDto:
    def __init__(
        self,
        group: Group,
        tasks: list[TaskDto],
        variants: list[VariantDto]
    ):
        self.title = str(group.title)
        self.id = int(group.id)
        self.tasks = tasks
        self.variants = variants
