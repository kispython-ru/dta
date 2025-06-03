from webapp.database import BaseRepository
from webapp.database.sqlalchemy import IDRepositoryMixin
from webapp.models.student import Student as Model


class StudentRepository(BaseRepository, IDRepositoryMixin):

    model = Model

    def get_all_by_group(self, group_id: int) -> list[Model] | None:
        students = self.get_many(group=group_id)
        return students if students else None

    def get_by_external_email(self, email: str, provider: str) -> Model | None:
        return self.get_one(email=email, provider=provider)

    def find_by_email(self, email: str) -> Model | None:
        email = email.lower()
        return self.get_one(email=email)

    def change_password(self, email: str, password: str) -> bool:
        email = email.lower()
        student = self.find_by_email(email)
        if student and student.unconfirmed_hash is None:
            self.update_one(student.id, {"unconfirmed_hash": password})
            return True
        return False

    def confirm(self, email: str) -> None:
        email = email.lower()
        student = self.find_by_email(email)
        if student and student.unconfirmed_hash is not None:
            self.update_one(
                student.id,
                {
                    "password_hash": student.unconfirmed_hash,
                    "unconfirmed_hash": None
                }
            )

    def create(self, email: str, password: str, teacher: bool = False) -> Model:
        email = email.lower()
        return self.add_n_return(data={
            "email": email,
            "unconfirmed_hash": password,
            "teacher": teacher,
            "blocked": False
        })

    def create_external(self, email: str, provider: str) -> Model: \
        return self.add_n_return(data={
            "email": email,
            "provider": provider,
            "blocked": False
        })

    def update_group(self, student: int, group: int | None) -> None:
        self.update_one(student, {"group": group})

    def update_variant(self, student: int, variant_id: int | None) -> None:
        self.update_one(student, {"variant": variant_id})
