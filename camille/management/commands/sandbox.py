from asyncio import run

from django.core.management.base import BaseCommand
from pydantic_ai import Agent


class Command(BaseCommand):
    help = "Mattermost agent"

    def handle(self, *args, **options):
        run(self.run())

    async def run(self):
        agent = Agent(model="google-gla:gemini-2.0-flash-lite-preview-02-05")

        res = await agent.run("What is the meaning of life?")
        print(res.output)
        usage = res.usage()
        print(usage.request_tokens, usage.response_tokens, usage.total_tokens)
