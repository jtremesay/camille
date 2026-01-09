from ..models.testing import MMTestObject
from .object import MMObjectClient


class MMTestObjectClient(MMObjectClient):
    obj_class = MMTestObject
    name = "object"
