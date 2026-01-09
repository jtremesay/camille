from datetime import datetime

from pydantic import BaseModel


class MMObject(BaseModel):
    @classmethod
    def from_json(cls, data: dict) -> "MMObject":
        return cls(**data)


class MMUser(MMObject):
    id: str
    created_at: datetime
    update_at: datetime
    delete_at: datetime
    username: str
    nickname: str
    first_name: str
    last_name: str

    @classmethod
    def from_json(cls, data: dict) -> "MMUser":
        return cls(
            id=data["id"],
            created_at=datetime.fromtimestamp(data["create_at"] / 1000),
            update_at=datetime.fromtimestamp(data["update_at"] / 1000),
            delete_at=datetime.fromtimestamp(data["delete_at"] / 1000),
            username=data["username"],
            nickname=data["nickname"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
