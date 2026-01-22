from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from camille.models import User


class Deps(BaseModel):
    user: User


def sp_user_context(ctx: RunContext[Deps]) -> str:
    return f"You are talking with:\n```json\r{ctx.deps.user.model_dump_json()}\n```"


def create_agent() -> Agent[Deps]:
    agent = Agent(
        "bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0", deps_type=Deps
    )
    agent.system_prompt(dynamic=True)(sp_user_context)

    return agent
