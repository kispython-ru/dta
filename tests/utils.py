import uuid


def unique_id() -> str:
    unique_id = uuid.uuid4()
    return str(unique_id)


def unique_id_int() -> int:
    unique_id = uuid.uuid4().node
    return int(unique_id)
