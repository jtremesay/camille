from typing import cast

from pydantic_ai import Agent as PAIAgent
from pydantic_ai import RunContext
from pydantic_ai._instructions import AgentInstruction
from pydantic_ai.capabilities import AbstractCapability as PAIAbstractCapability

from camille.models import AgentPersonality


class PersonalityCapability(PAIAbstractCapability):
    def __init__(self, personality: AgentPersonality) -> None:
        self.personality = personality

    def get_instructions(self) -> AgentInstruction:
        def _instr(ctx: RunContext[object]) -> str:
            return cast(str, self.personality.template).format(
                agent_name=cast(PAIAgent, ctx.agent).name
            )

        return _instr
