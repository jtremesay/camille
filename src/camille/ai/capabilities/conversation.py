from json import dumps
from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability

from camille.ai.deps import Deps


class ConversationCapability(AbstractCapability):
    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[Deps]) -> str:
            return render_to_string(
                "camille/ai/instructions/conversation.md",
                {
                    "all_users": [
                        dumps({
                            "id": u.id,
                            "username": u.username,
                            "first_name": u.first_name,
                            "last_name": u.last_name,
                        })
                        for u in ctx.deps.all_users
                    ],
                    "current_user": ctx.deps.current_user,
                },
            )

        return inner
