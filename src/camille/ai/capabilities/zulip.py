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

from collections.abc import Awaitable, Callable
from mimetypes import guess_type
from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import FunctionToolset, ModelRetry, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import BinaryContent, BinaryImage, ToolCallPart
from pydantic_ai.tools import ToolDefinition

from camille.ai.capabilities.image_tools import IMAGE_TOOL_NAMES
from camille.ai.deps import ZulipDeps


class ZulipToolset(FunctionToolset):
    def __init__(self):
        super().__init__(id="zulip")

        @self.tool()
        async def get_zulip_file(
            ctx: RunContext[ZulipDeps], file_id: str
        ) -> BinaryContent:
            """Get the contents of a Zulip file by its ID (its `/user_uploads/...` path)."""
            if (content := await ctx.deps.get_file(file_id)) is None:
                raise ModelRetry(f"Zulip file {file_id} not found")

            return content

        @self.tool()
        async def add_file_to_zulip_message(
            ctx: RunContext[ZulipDeps], filename: str, content: bytes | str
        ) -> None:
            """Add a file to the message you are writing."""
            if isinstance(content, str):
                content = content.encode()
            await ctx.deps.upload_file(
                BinaryContent(
                    content,
                    media_type=guess_type(filename)[0] or "application/octet-stream",
                ),
                filename=filename,
            )


class ZulipCapability(AbstractCapability):
    def get_toolset(self) -> ZulipToolset:
        return ZulipToolset()

    async def wrap_tool_execute(
        self,
        ctx: RunContext[Any],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        handler: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> Any:
        result = await handler(args)
        if tool_def.name not in IMAGE_TOOL_NAMES:
            return result
        if not isinstance(ctx.deps, ZulipDeps):
            raise TypeError("Image tools in Zulip require ZulipDeps")
        if not isinstance(result, BinaryContent) or not result.is_image:
            raise TypeError(
                f"Image tool {tool_def.name!r} returned a non-image result"
            )

        file_id = await ctx.deps.upload_file(result)
        image = BinaryImage(
            result.data,
            media_type=result.media_type,
            identifier=file_id,
        )
        return [f"Zulip file ID: {file_id}", image]

    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[ZulipDeps]) -> str:
            return render_to_string(
                "camille/ai/instructions/zulip.md",
                {
                    "channel_name": ctx.deps.channel_name,
                },
            )

        return inner
