from asyncio import run

from django.core.management.base import BaseCommand
from pydantic_ai import Agent, ModelHTTPError, TextPart


class Command(BaseCommand):
    help = "Mattermost agent"

    def handle(self, *args, **options):
        run(self.ahandle(*args, **options))

    async def ahandle(self, *args, **options):
        agent = Agent(
            "ollama:gemma4:e2b",
            system_prompt="You are an agent under evaluation in a sandbox.",
        )

        @agent.tool_plain
        async def the_tool() -> None:
            pass

        try:
            async with agent.iter("call the tool `the_tool`") as run:
                async for node in run:
                    if agent.is_call_tools_node(node):
                        for part in node.model_response.parts:
                            if isinstance(part, TextPart):
                                print(part.content)
        except ModelHTTPError as e:
            if (
                e.status_code == 400
                and e.body
                and e.body.get("error") == "invalid message content type: <nil>"
            ):
                print("(no output)")
            else:
                raise
