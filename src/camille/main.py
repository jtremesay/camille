from asyncio import run

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent

load_dotenv()

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()

agent = Agent("bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0")


async def amain():
    await agent.to_cli()


def main():
    run(amain())
