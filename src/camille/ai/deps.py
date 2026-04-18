from dataclasses import dataclass

from django.contrib.auth.models import User


@dataclass
class Deps:
    agent_name: str
    current_user: User  # User that triggered the agent execution, used for permissions and context
    all_users: list[
        User
    ]  # All users in the conversation, used for context and permissions


@dataclass
class MattermostDeps(Deps):
    channel_name: str
