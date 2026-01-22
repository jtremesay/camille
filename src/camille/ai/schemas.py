from typing import Optional

from ninja import Schema


class UserSchema(Schema):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileSchema(Schema):
    user: UserSchema
    model_name: Optional[str] = None
    notes: Optional[str] = None
