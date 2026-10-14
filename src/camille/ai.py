from typing import cast

from pydantic_ai import Agent as PAIAgent

from .capabilities.personality import PersonalityCapability
from .models import Agent, AgentPersonality


def create_pai_agent(agent: Agent, name: str = "Camille") -> PAIAgent:
    tools = []
    capabilities = []

    if agent.personality is not None:
        capabilities.append(
            PersonalityCapability(
                personality=cast(AgentPersonality, agent.personality), agent_name=name
            )
        )

    pai_agent = PAIAgent(
        model=agent.get_model_instance(),
        tools=tools,
        capabilities=capabilities,
    )

    return pai_agent
