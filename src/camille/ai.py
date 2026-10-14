from typing import cast

from pydantic_ai import Agent as PAIAgent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from .capabilities.personality import PersonalityCapability
from .models import Agent, AgentPersonality


def create_pai_agent(agent: Agent, name: str = "Camille") -> PAIAgent:
    tools = []
    capabilities = []

    # Add personality capability if needed
    if (personality := agent.personality) is not None:
        capabilities.append(
            PersonalityCapability(
                personality=cast(AgentPersonality, personality), agent_name=name
            )
        )

    # Add DuckDuckGo search tool if enabled
    if agent.ddg_enable:
        tools.append(duckduckgo_search_tool)

    pai_agent = PAIAgent(
        model=agent.get_model_instance(),
        tools=tools,
        capabilities=capabilities,
    )

    return pai_agent
