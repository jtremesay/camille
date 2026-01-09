from typing import cast

from ..models.user import MMUser
from .object import MMObjectClient


class MMUserClient(MMObjectClient):
    obj_class = MMUser
    name = "user"

    async def get_me(self) -> MMUser:
        return cast(MMUser, await self.get("me"))
