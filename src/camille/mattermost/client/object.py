from typing import TYPE_CHECKING

from ..models.object import MMObject

if TYPE_CHECKING:
    from .client import MattermostClient


class MMObjectClient:
    obj_class: type[MMObject]
    name: str

    def __init__(self, client: "MattermostClient"):
        self.client = client

    async def get(self, object_id: str) -> MMObject:
        data = await self.client.get(f"/{self.name}s/{object_id}")
        return self.obj_class.from_json(data)
