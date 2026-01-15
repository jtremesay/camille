from dataclasses import dataclass

from camille.models import MMChannel, MMUser


@dataclass
class Dependency:
    channel: MMChannel
    users: dict[str, MMUser]
