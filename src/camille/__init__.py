#!/usr/bin/env python3
import asyncio
import logging
from collections.abc import Sequence
from os import environ
from pathlib import Path
from string import Template
from typing import Optional

import logfire
from dotenv import load_dotenv
from httpx import AsyncClient
from pydantic import BaseModel
from pydantic_ai import models
from pydantic_ai.agent import Agent

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
PROMPT_FILE = BASE_DIR / "prompt.txt"


class CamilleAgent(Agent):
    def __init__(
        self,
        *args,
        model: Optional[models.Model | models.KnownModelName | str] = None,
        system_prompt: str | Sequence[str] = (),
        name: Optional[str] = None,
        **kwargs,
    ):
        if model is None:
            model = environ.get("CAMILLE_MODEL")

        if not system_prompt and name:
            try:
                prompt_tpl_text = PROMPT_FILE.read_text()
            except FileNotFoundError:
                pass
            else:
                prompt_tpl = Template(prompt_tpl_text)
                system_prompt = prompt_tpl.substitute(
                    agent_name=name,
                )

        super().__init__(
            *args, model=model, system_prompt=system_prompt, name=name, **kwargs
        )


class User(BaseModel):
    id: str
    username: str
    nickname: str
    first_name: str
    last_name: str


class MattermostClient(AsyncClient):
    def __init__(self, base_url: str, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        super().__init__(base_url=base_url, headers=headers)

    @classmethod
    def create(cls) -> "MattermostClient":
        return cls(
            base_url=environ["MATTERMOST_HOST"] + "/api/v4/",
            access_token=environ["MATTERMOST_ACCESS_TOKEN"],
        )

    async def get_user(self, user_id: str) -> User:
        response = await self.get(f"users/{user_id}")
        response.raise_for_status()
        return User.model_validate_json(response.content)

    async def get_me(self) -> User:
        return await self.get_user("me")


def load_docker_secrets() -> None:
    # Search all environment variables that end with _FILE.
    # We do it first to avoid modifying the environ dictionary while iterating over it.
    secrets_keys = [key for key in environ.keys() if key.endswith("_FILE")]

    # Read the secrets from the files and set them as environment variables
    base_path = Path("/") / "run" / "secrets"
    if not base_path.exists():
        return

    for secret_key in secrets_keys:
        secret_path = base_path / environ[secret_key]
        try:
            secret = secret_path.read_text().strip()
        except FileNotFoundError:
            continue

        key = secret_key[:-5]  # Remove the _FILE suffix
        environ[key] = secret  # Set the environment variable


def load_env():
    load_docker_secrets()
    load_dotenv()


async def amain():
    logging.basicConfig(level=logging.INFO)

    # Load environment variables
    load_env()

    # Configure Logfire
    logfire.configure(
        token=environ.get("LOGFIRE_TOKEN"),
        environment=environ.get("LOGFIRE_ENV", "production"),
        send_to_logfire="if-token-present",
    )
    logfire.instrument_httpx(capture_all=True)
    logfire.instrument_pydantic_ai()

    # agent = CamilleAgent(name="Camille")

    async with MattermostClient.create() as client:
        me = await client.get_me()
        logger.info("Logged in as %s (@%s)", me.first_name, me.username)


def main():
    asyncio.run(amain())
