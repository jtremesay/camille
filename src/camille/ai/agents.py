from pydantic_ai import Agent

from camille.ai import system_prompts, tools
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
        toolsets=[tools.user_toolset, tools.thread_toolset],
    )
    agent.system_prompt(dynamic=True)(system_prompts.personality_context)
    agent.system_prompt(dynamic=True)(system_prompts.thread_context)
    agent.system_prompt(dynamic=True)(system_prompts.user_profile_context)
    return agent
