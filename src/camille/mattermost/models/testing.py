from datetime import datetime

from .object import MMObject


class MMTestObject(MMObject):
    id: int
    name: str
    is_active: bool
    gender: float
    birthdate: datetime
