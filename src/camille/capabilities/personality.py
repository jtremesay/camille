from typing import cast

from pydantic_ai.capabilities import AbstractCapability as PAIAbstractCapability

from camille.models import AgentPersonality


class PersonalityCapability(PAIAbstractCapability):
    def __init__(self, personality: AgentPersonality, agent_name: str) -> None:
        self.personality = personality
        self.agent_name = agent_name

    def get_instructions(self) -> str:
        return cast(str, self.personality.template).format(agent_name=self.agent_name)
