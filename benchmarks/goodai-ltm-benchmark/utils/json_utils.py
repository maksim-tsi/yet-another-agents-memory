import dataclasses
from datetime import datetime
from enum import Enum
from json import JSONEncoder
from typing import Any


class LLMJSONError(Exception):
    pass


class CustomEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.timestamp()
        if isinstance(o, Enum):
            return o.value
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)

        return super().default(o)
