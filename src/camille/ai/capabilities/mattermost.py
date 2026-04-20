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

from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import FunctionToolset, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import BinaryContent

from camille.ai.deps import MattermostDeps


class MattermostToolset(FunctionToolset):
    def __init__(self):
        super().__init__(id="mattermost")

        @self.tool()
        async def get_mattermost_file(
            ctx: RunContext[MattermostDeps], file_id: str
        ) -> BinaryContent:
            """Get the contents of a Mattermost file by its ID."""
            r = await ctx.deps.mattermost_client.get(f"/files/{file_id}")
            r.raise_for_status()

            return BinaryContent(
                r.content,
                media_type=r.headers.get("Content-Type", "application/octet-stream"),
            )

        @self.tool()
        async def add_file_to_mattermost_post(
            ctx: RunContext[MattermostDeps], filename: str, content: bytes | str
        ) -> None:
            """Add a file to the post you are writing."""
            r = await ctx.deps.mattermost_client.post(
                "/files",
                content=content,
                params={
                    "channel_id": ctx.deps.channel_id,
                    "filename": filename,
                },
            )
            r.raise_for_status()

            file_id = r.json()["file_infos"][0]["id"]
            ctx.deps.generated_files_ids.append(file_id)


class MattermostCapability(AbstractCapability):
    def get_toolset(self) -> MattermostToolset:
        return MattermostToolset()

    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[MattermostDeps]) -> str:
            return render_to_string(
                "camille/ai/instructions/mattermost.md",
                {
                    "channel_name": ctx.deps.channel_name,
                },
            )

        return inner
