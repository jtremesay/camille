from dataclasses import dataclass

from camille.models import (
    Profile,
)


@dataclass
class Deps:
    profile: Profile
