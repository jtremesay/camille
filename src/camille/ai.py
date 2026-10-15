from logging import getLogger
from typing import cast

from ddgs.ddgs import DDGS, DDGSException
from exa_py import AsyncExa
from pydantic_ai import Agent as PAIAgent
from pydantic_ai import ImageGenerator
from pydantic_ai.capabilities import ImageGeneration, WebFetch
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai_harness import CodeMode, ExaSearch, Planning, SubAgent, SubAgents

from pydanticai_django.planning import DjangoPlanStore

from .capabilities.personality import PersonalityCapability
from .models import Agent, AgentPersonality, AIImageModel, ExaApiKey, TavilyApiKey

logger = getLogger(__name__)


class MyDDGS(DDGS):
    def _search_sync(self, *args, **kwargs):
        # https://github.com/pydantic/pydantic-ai/issues/9820
        try:
            return super()._search_sync(*args, **kwargs)
        except DDGSException as e:
            logger.error(f"DDGS search failed: {e}")

            return []


def create_pai_agent(
    agent: Agent, name: str = "Camille", planning_session_id: str | None = None
) -> PAIAgent:
    tools = []
    capabilities = []

    # Add personality capability if needed
    if (personality := cast(AgentPersonality | None, agent.personality)) is not None:
        capabilities.append(PersonalityCapability(personality=personality))

    # Add planning capability if enabled
    if agent.planning_enabled:
        if planning_session_id is None:
            raise ValueError(
                "Planning session ID must be provided if planning is enabled."
            )
        capabilities.append(
            Planning(
                store=DjangoPlanStore(session_id=planning_session_id),
                enable_subtasks=True,
            )
        )

    # Add code mode capability if enabled
    if agent.codemode_enabled:
        capabilities.append(CodeMode())

    # Add DuckDuckGo search tool if enabled
    if agent.ddg_enabled:
        capabilities.append(
            WebFetch(
                id="duckduckgo_search",
                local=duckduckgo_search_tool(duckduckgo_client=MyDDGS()),
            )
        )

    # Add Exa search tool if enabled
    if agent.exa_enabled:
        if (exa_api_key := cast(ExaApiKey | None, agent.exa_api_key)) is not None:
            capabilities.append(
                ExaSearch(client=AsyncExa(api_key=cast(str, exa_api_key.key)))
            )
        else:
            raise ValueError("Exa search tool is enabled but no API key is set.")

    # Add Tavily search tool if enabled
    if agent.tavily_enabled:
        if (
            tavily_api_key := cast(TavilyApiKey | None, agent.tavily_api_key)
        ) is not None:
            capabilities.append(
                WebFetch(
                    id="tavily_search",
                    local=tavily_search_tool(api_key=cast(str, tavily_api_key.key)),
                )
            )
        else:
            raise ValueError("Tavily search tool is enabled but no API key is set.")

    # Add image generation capability if enabled
    if agent.imgen_enabled:
        if (imgen_model := cast(AIImageModel | None, agent.imgen_model)) is not None:
            generator = ImageGenerator(
                model=imgen_model.get_instance(),
            )
        else:
            raise ValueError("Image generation is enabled but no model is set.")

        capabilities.append(ImageGeneration(local=generator))

    # Add sub-agents if any
    if sub_agents := [
        SubAgent(agent=create_pai_agent(sub_agent, name=sub_agent.name))
        for sub_agent in agent.sub_agents.all()
    ]:
        capabilities.append(SubAgents(agents=sub_agents))

    pai_agent = PAIAgent(
        model=agent.get_model_instance(),
        tools=tools,
        capabilities=capabilities,
        name=name,
    )

    return pai_agent
