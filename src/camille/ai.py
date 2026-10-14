from pydantic_ai import Agent as PAIAgent

from .models import Agent


def create_pai_agent(agent: Agent) -> PAIAgent:
    tools = []
    capabilities = []
    pai_agent = PAIAgent(
        model="google:gemini-3.5-flash-lite",
        tools=tools,
        capabilities=capabilities,
    )

    return pai_agent
