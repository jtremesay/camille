from datetime import datetime
from typing import cast

from .client import MMObjectClient
from .models import MMObject


class MMTestObject(MMObject):
    id: int
    name: str
    is_active: bool
    gender: float
    birthdate: datetime

    @classmethod
    def from_json(cls, data: dict) -> "MMTestObject":
        return cast(MMTestObject, super().from_json(data))


class MMTestObjectClient(MMObjectClient):
    obj_class = MMTestObject
    name = "testobject"
