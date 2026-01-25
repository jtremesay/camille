from dataclasses import dataclass

from camille.ai.deps import Dependency as BaseDependency
from camille.models import MMChannel, MMUser


@dataclass
class Dependency(BaseDependency):
    channel: MMChannel
    users: dict[str, MMUser]
