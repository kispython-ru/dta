import uuid


def unique_str() -> str:
    unique_id = uuid.uuid4()
    return str(unique_id)


def unique_int() -> int:
    unique_id = uuid.uuid4().node
    return int(unique_id)
