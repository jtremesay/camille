# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from collections.abc import Sequence

import logfire
from asgiref.sync import sync_to_async
from ddgs.ddgs import DDGS, DDGSException
from pydantic_ai import Agent
from pydantic_ai.capabilities import AbstractCapability, ImageGeneration
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool

from camille.ai.capabilities.agpl import AGPLCapability
from camille.ai.capabilities.conversation import ConversationCapability
from camille.ai.capabilities.current_time import CurrentTimeCapability
from camille.ai.capabilities.instructions import InstructionsCapability
from camille.ai.capabilities.memory import MemoryCapability
from camille.ai.capabilities.personality import PersonalityCapability
from camille.ai.deps import Deps
from camille.ai.image_models import create_image_model_for_user
from camille.models import AgentConfig

IMAGE_GENERATION_TOOL_NAME = "generate_image"


class MyDDGS(DDGS):
    def _search_sync(self, *args, **kwargs):
        # https://github.com/pydantic/pydantic-ai/issues/9820
        try:
            return super()._search_sync(*args, **kwargs)
        except DDGSException as e:
            logfire.error(f"DDGS search failed: {e}")
            return []


async def create_agent_from_config(
    config: AgentConfig,
    capabilities: Sequence[AbstractCapability] | None = None,
) -> Agent:
    """Build an agent tailored to the given user configuration.

    The agent is built on demand so that each user only gets the capabilities
    enabled by its own configuration. Capabilities specific to the caller
    (e.g. the Mattermost ones) are passed through `capabilities`.
    """
    all_capabilities: list[AbstractCapability] = [
        PersonalityCapability(),
        AGPLCapability(),
        ConversationCapability(),
        InstructionsCapability(),
        MemoryCapability(),
        CurrentTimeCapability(),
        *(capabilities or []),
    ]

    if config.model_image:
        user = await sync_to_async(getattr)(config, "user")
        all_capabilities.append(
            ImageGeneration(
                native=False,
                fallback_image_model=await create_image_model_for_user(
                    user, config.model_image
                ),
            )
        )

    return Agent(
        deps_type=Deps,
        capabilities=all_capabilities,
        tools=[duckduckgo_search_tool(MyDDGS()), web_fetch_tool()],
    )
