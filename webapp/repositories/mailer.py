from sqlalchemy import exists, select
from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.mailer import Mailer as Model


class MailerRepository(BaseRepository, IDRepositoryMixin):
    model = Model

    def exists(self, domain: str) -> bool:
        stmt = select(exists().where(self.model.domain == domain))
        result = (self.execute(stmt)).scalar()
        return result

    def get_domains(self) -> list[str]:
        stmt = select(self.model.domain)
        return (self.execute(stmt)).scalars().all()

    def create(self, domain: str) -> Model:
        domain = domain.lower()
        return self.add_n_return(data={"domain": domain})
