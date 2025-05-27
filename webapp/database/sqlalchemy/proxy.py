from typing import Any
from .context import DbContextManager


class RepositoryProxy:
    def __init__(
            self, repository_cls, db_context_manager: DbContextManager
    ) -> None:
        self.repository_cls = repository_cls
        self.db_context_manager = db_context_manager

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self.repository_cls, name)

        if callable(attr):
            def wrapper(*args, **kwargs):
                with self.db_context_manager.create_session() as session:
                    repo_instance = self.repository_cls(session)
                    method = getattr(repo_instance, name)
                    return method(*args, **kwargs)
            return wrapper
        else:
            return attr
