from pydantic import BaseModel


class MMObject(BaseModel):
    @classmethod
    def from_json(cls, data: dict) -> "MMObject":
        return cls(**data)
