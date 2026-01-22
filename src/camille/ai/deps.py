from dataclasses import dataclass

from camille.models import (
    LLMThread,
    Profile,
)


@dataclass
class Deps:
    profile: Profile
    thread: LLMThread
    agent_name: str = "Camille"
