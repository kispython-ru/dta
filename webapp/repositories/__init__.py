from typing import Callable

from webapp.database.sqlalchemy.context import DbContextManager
from webapp.database.sqlalchemy.proxy import RepositoryProxy
from .allowed_ip import AllowedIpRepository
from .final_seed import FinalSeedRepository
from .group import GroupRepository
from .mailer import MailerRepository
from .message import MessageRepository
from .message_check import MessageCheckRepository
from .student import StudentRepository
from .task import TaskRepository
from .task_status import TaskStatusRepository
from .variant import VariantRepository

__all__ = [
    AllowedIpRepository.__name__,
    FinalSeedRepository.__name__,
    GroupRepository.__name__,
    MailerRepository.__name__,
    MessageRepository.__name__,
    MessageCheckRepository.__name__,
    StudentRepository.__name__,
    TaskRepository.__name__,
    TaskStatusRepository.__name__,
    VariantRepository.__name__,
]


class AppDatabase:
    def __init__(self, get_connection: Callable[[], str]):
        db = DbContextManager(get_connection)
        self.groups: GroupRepository = RepositoryProxy(GroupRepository, db)
        self.variants: VariantRepository = RepositoryProxy(
            VariantRepository, db
        )
        self.tasks: TaskRepository = RepositoryProxy(TaskRepository, db)
        self.statuses: TaskStatusRepository = RepositoryProxy(
            TaskStatusRepository, db
        )
        self.messages: MessageRepository = RepositoryProxy(
            MessageRepository, db
        )
        self.checks: MessageCheckRepository = RepositoryProxy(
            MessageCheckRepository, db
        )
        self.seeds: FinalSeedRepository = RepositoryProxy(
            FinalSeedRepository, db
        )
        self.students: StudentRepository = RepositoryProxy(
            StudentRepository, db
        )
        self.mailers: MailerRepository = RepositoryProxy(MailerRepository, db)
        self.ips: AllowedIpRepository = RepositoryProxy(AllowedIpRepository, db)
