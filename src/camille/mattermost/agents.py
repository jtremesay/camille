from pydantic_ai import Agent

from camille.ai.agents import create_agent_for_user as base_create_agent_for_user
from camille.mattermost.deps import Dependency
from camille.mattermost.prompts import mm_system_prompt
from camille.models import MMUser


async def create_agent_for_user(
    user: MMUser, deps_class: type[Dependency]
) -> Agent[Dependency]:
    agent = await base_create_agent_for_user(user=user, deps_class=deps_class)
    agent.system_prompt(dynamic=True)(mm_system_prompt)
    return agent
