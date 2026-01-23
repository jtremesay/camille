from dataclasses import dataclass

from camille.http import HtttPClient
from camille.models import (
    LLMThread,
    Profile,
)


@dataclass
class Deps:
    profile: Profile
    thread: LLMThread
    agent_name: str = "Camille"
    http_client: HtttPClient = HtttPClient()
