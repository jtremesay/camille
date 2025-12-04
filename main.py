#!/usr/bin/env python3
import asyncio
import logging
from os import environ
from pathlib import Path

import logfire
from dotenv import load_dotenv
from httpx import AsyncClient

logger = logging.getLogger(__name__)


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


async def main():
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

    async with AsyncClient() as client:
        pass


if __name__ == "__main__":
    asyncio.run(main())
