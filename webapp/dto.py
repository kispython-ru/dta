from typing import Dict, List, Union

from flask import Config

from webapp.models import Group, Task, TaskStatus, TaskStatusEnum, Variant


class ExternalTaskDto:
    def __init__(self, group_title: str, task: int, variant: int):
        self.group_title = group_title
        self.task = task
        self.variant = variant


class TaskDto:
    def __init__(self, group: Group, task: Task, base_url: str):
        self.id = int(task.id)
        self.formulation_url = f'{base_url}/{self.id}/{group.title}.html'


class TaskStatusDto:
    def __init__(
        self,
        group: Group,
        variant: Variant,
        task: TaskDto,
        status: Union[TaskStatus, None],
        external: ExternalTaskDto,
        base_url: str,
    ) -> None:
        self.task = task.id
        self.variant = variant.id
        self.group = int(group.id)
        self.group_title = group.title
        self.base_url = base_url
        self.external = external

        ns = TaskStatusEnum.NotSubmitted
        self.status = ns if status is None else TaskStatusEnum(status.status)
        self.checked = self.status == TaskStatusEnum.Checked
        self.error_message = None if status is None or \
            status.output is None else status.output

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
            TaskStatusEnum.Submitted: "inherit",
            TaskStatusEnum.Checking: "inherit",
            TaskStatusEnum.Checked: "#e3ffee",
            TaskStatusEnum.Failed: "#ffe3ee",
            TaskStatusEnum.NotSubmitted: "inherit",
        })

    @property
    def name(self) -> str:
        return self.map_status({
            TaskStatusEnum.Submitted: "Отправлено",
            TaskStatusEnum.Checking: "Проверяется",
            TaskStatusEnum.Checked: "Принято",
            TaskStatusEnum.Failed: "Ошибка!",
            TaskStatusEnum.NotSubmitted: "Не отправлено",
        })

    @property
    def code(self) -> str:
        return self.map_status({
            TaskStatusEnum.Submitted: "?",
            TaskStatusEnum.Checking: "...",
            TaskStatusEnum.Checked: "+",
            TaskStatusEnum.Failed: "x",
            TaskStatusEnum.NotSubmitted: "-",
        })

    @property
    def color(self) -> str:
        return self.map_status({
            TaskStatusEnum.Submitted: "primary",
            TaskStatusEnum.Checking: "warning",
            TaskStatusEnum.Checked: "success",
            TaskStatusEnum.Failed: "danger",
            TaskStatusEnum.NotSubmitted: "secondary",
        })

    def map_status(self, map: Dict[TaskStatusEnum, str]):
        return map[self.status]


class VariantDto:
    def __init__(self, variant: Variant, statuses: List[TaskStatusDto]):
        self.id = int(variant.id)
        self.statuses = statuses


class GroupDto:
    def __init__(
        self,
        group: Group,
        tasks: List[TaskDto],
        variants: List[VariantDto]
    ):
        self.title = str(group.title)
        self.id = int(group.id)
        self.tasks = tasks
        self.variants = variants


class AppConfig:
    def __init__(self, config: Config):
        self.highlight_syntax: bool = config["HIGHLIGHT_SYNTAX"]
        self.core_path: str = config["CORE_PATH"]
        self.csv_token: str = config["CSV_TOKEN"]
        self.api_token: str = config["API_TOKEN"]
        self.connection_string: str = config["CONNECTION_STRING"]
        self.task_base_url: str = config["TASK_BASE_URL"]
        self.no_background_worker: bool = config["DISABLE_BACKGROUND_WORKER"]
