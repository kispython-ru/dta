from sqlalchemy import literal

from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.allowed_ip import AllowedIp as Model


class AllowedIpRepository(BaseRepository, IDRepositoryMixin):
    model = Model

    def is_allowed(self, ip: str) -> bool:
        self.get_by_id
        return bool(self.count(literal(ip).contains(self.model.ip)))

    def list_allowed(self) -> list[Model]:
        return self.get_all()

    def allow(self, ip: str, label: str) -> Model:
        return self.add_n_return(data={"ip": ip, "label": label})

    def disallow(self, id: int) -> None:
        self.delete_one(id)
