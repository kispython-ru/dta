import uuid


def unique_id() -> str:
    id = uuid.uuid4()
    return str(id)
