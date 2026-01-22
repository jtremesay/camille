from pydantic_ai import Agent

from camille.ai.deps import Deps
from camille.ai.models import create_model_for_profile
from camille.ai.system_prompts import user_profile_context as sp_user_profile_context
from camille.models import (
    Profile,
)


def create_agent_for_profile(profile: Profile) -> Agent[Deps]:
    agent = Agent(
        create_model_for_profile(
            profile,
        ),
        deps_type=Deps,
    )
    agent.system_prompt(dynamic=True)(sp_user_profile_context)

    return agent
