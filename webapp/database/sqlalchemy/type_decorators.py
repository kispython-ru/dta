from sqlalchemy import TypeDecorator, Text, Integer
from json import loads, dumps


class IntEnum(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value
        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)


class JsonArray(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if not value:
            return '[]'
        if isinstance(value, list):
            return dumps(value)
        raise ValueError("Bad value type for JSON array.")

    def process_result_value(self, value, dialect):
        if not value:
            return []
        return loads(value)
