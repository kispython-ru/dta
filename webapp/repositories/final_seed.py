from typing import Any
import uuid

from sqlalchemy import delete, update

from webapp.database import BaseRepository
from webapp.models.final_seed import FinalSeed as Model


class FinalSeedRepository(BaseRepository):
    model = Model

    def update_one(self, group: int, data: dict[str, Any]) -> None:
        stmt = (
            update(self.model).where(self.model.group == group).values(**data)
        )
        self.execute(stmt)

    def delete_one(self, group: int) -> None:
        stmt = delete(self.model).where(self.model.group == group)
        self.execute(stmt)

    def get_final_seed(self, group: int) -> Model | None:
        return self.get_one(group=group)

    def begin_final_test(self, group: int) -> Model:
        seed = str(uuid.uuid4())
        return self.add_n_return(
            data={"group": group, "seed": seed, "active": True}
        )

    def continue_final_test(self, group: int) -> None:
        seed = self.get_final_seed(group)
        if seed:
            self.update_one(seed.group, {"active": True})

    def end_final_test(self, group: int) -> None:
        seed = self.get_final_seed(group)
        if seed:
            self.update_one(seed.group, {"active": False})

    def delete_final_seed(self, group: int) -> None:
        seed = self.get_final_seed(group)
        if seed:
            self.delete_one(seed.group)
