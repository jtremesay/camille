from typing import Optional

from ninja import Schema


class UserSchema(Schema):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileSchema(Schema):
    id: int
    user: UserSchema
    model_name: Optional[str] = None
    personality_id: Optional[int] = None
    notes: Optional[str] = None


class AgentPersonalitySchema(Schema):
    id: int
    name: str
    description: str
    prompt_template: str
