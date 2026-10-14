from logging import getLogger
from typing import cast

from ddgs.ddgs import DDGS, DDGSException
from exa_py import AsyncExa
from pydantic_ai import Agent as PAIAgent
from pydantic_ai import ImageGenerator
from pydantic_ai.capabilities import ImageGeneration
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai_harness import ExaSearch

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
    if agent.ddg_enabled:
        tools.append(duckduckgo_search_tool(duckduckgo_client=MyDDGS()))

    # Add web fetch tool if enabled
    if agent.webfetch_enabled:
        tools.append(web_fetch_tool())

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
            tools.append(tavily_search_tool(api_key=cast(str, tavily_api_key.key)))
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

    pai_agent = PAIAgent(
        model=agent.get_model_instance(),
        tools=tools,
        capabilities=capabilities,
    )

    return pai_agent
