from dataclasses import dataclass

from camille.models import MMUser


@dataclass
class Dependency:
    me: MMUser
    sender: MMUser
