import warnings

from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.variant import Variant as Model
from webapp.repositories.message import MessageRepository


class VariantRepository(BaseRepository, IDRepositoryMixin):

    model = Model

    def get_by_id(self, variant_id: int) -> Model | None:
        return super().get_by_id(variant_id)

    def create_by_ids(self, ids: list[int]) -> list[Model]:
        return [
            self.add_n_return(data={"id": variant_id})
            for variant_id in ids
        ]

    @warnings.deprecated(
        "get_student_variants() in this repository is deprecated. "
        + "Use MessageRepository::get_student_variants() instead."
    )
    def get_student_variants(self, student: int, group: int) -> list[int]:
        message_repo: MessageRepository = MessageRepository(self.session)
        return message_repo.get_student_variants(student, group)
