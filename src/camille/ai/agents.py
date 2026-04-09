from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool

from camille.ai.deps import Dependency
from camille.ai.models import create_model_for_user
from camille.ai.prompts import personality_prompt
from camille.ai.tools import toolsets as ai_toolsets
from camille.models import MMUser


async def create_agent_for_user(
    user: MMUser,
    deps_class=Dependency,
    tools: Optional[list] = None,
    toolsets: Optional[list] = None,
) -> Agent[Dependency]:
    if tools is None:
        tools = []

    tools.extend(
        [
            duckduckgo_search_tool(),
            web_fetch_tool(),
        ]
    )

    if toolsets is None:
        toolsets = []

    toolsets.extend(ai_toolsets)

    agent = Agent(
        model=await create_model_for_user(user),
        deps_type=deps_class,
        tools=tools,
        toolsets=toolsets,
    )
    agent.system_prompt(dynamic=True)(personality_prompt)

    return agent
