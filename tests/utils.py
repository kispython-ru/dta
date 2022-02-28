import uuid


def unique_id() -> str:
    unique_id = uuid.uuid4()
    return str(unique_id)
