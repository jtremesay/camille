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

from collections.abc import Iterator, Sequence
from typing import Any

from pydantic_ai import FunctionToolset, ModelRetry, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.exceptions import ContentFilterError
from pydantic_ai.images import ImageGenerationModel, ImageGenerator
from pydantic_ai.messages import (
    BinaryContent,
    BinaryImage,
    FilePart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolReturnPart,
    UserPromptPart,
)

from camille.ai.deps import Deps

IMAGE_EDITING_TOOL_NAME = "edit_image"


def iter_binary_contents(messages: Sequence[ModelMessage]) -> Iterator[BinaryContent]:
    """Iterate over all binary contents held by the conversation messages."""

    def flatten(content: Any) -> Iterator[BinaryContent]:
        if isinstance(content, BinaryContent):
            yield content
        elif isinstance(content, (list, tuple)):
            for item in content:
                yield from flatten(item)

    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, (ToolReturnPart, UserPromptPart)):
                    yield from flatten(part.content)
        elif isinstance(message, ModelResponse):
            for part in message.parts:
                if isinstance(part, FilePart):
                    yield part.content


async def resolve_image(ctx: RunContext[Deps], image_id: str) -> BinaryImage:
    """Find an image by its identifier in the conversation, or fetch it as a file."""
    # Most recent first, in case of duplicated identifiers
    for content in reversed(list(iter_binary_contents(ctx.messages))):
        if content.identifier == image_id:
            break
    else:
        content = await ctx.deps.get_file(image_id)

    if content is None:
        raise ModelRetry(f"Image {image_id!r} not found")
    if not content.is_image:
        raise ModelRetry(
            f"File {image_id!r} is not an image (media type: {content.media_type})"
        )

    return BinaryImage(content.data, media_type=content.media_type)


class ImageEditingToolset(FunctionToolset):
    def __init__(self, generator: ImageGenerator):
        super().__init__(id="image_editing")

        @self.tool(name=IMAGE_EDITING_TOOL_NAME)
        async def edit_image(
            ctx: RunContext[Deps], prompt: str, image_ids: list[str]
        ) -> BinaryImage:
            """Edit or transform one or more existing images according to the prompt.

            Args:
                prompt: Description of the changes to apply to the image(s).
                image_ids: Identifiers of the reference images, in order. Use the
                    file identifier of an image previously generated, edited or
                    retrieved in the conversation (as given by "See file <id>"),
                    or the ID of a file attached by the user.
            """
            if not image_ids:
                raise ModelRetry("At least one image ID is required")

            images = [await resolve_image(ctx, image_id) for image_id in image_ids]
            try:
                result = await generator.generate(prompt, images=images)
            except ContentFilterError as e:
                raise ModelRetry(str(e)) from e

            return result.image


class ImageEditingCapability(AbstractCapability):
    """Edit images attached to, or generated in, the conversation."""

    def __init__(self, image_model: ImageGenerationModel):
        self.generator = ImageGenerator(image_model)

    def get_toolset(self) -> ImageEditingToolset:
        return ImageEditingToolset(self.generator)
