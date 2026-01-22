from pydantic_ai import Agent

from camille.ai import system_prompts
from camille.ai.deps import Deps
from camille.ai.models import create_model_for_profile
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
    agent.system_prompt(dynamic=True)(system_prompts.personality_context)
    agent.system_prompt(dynamic=True)(system_prompts.user_profile_context)
    return agent
