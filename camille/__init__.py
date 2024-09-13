# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
import os
from argparse import ArgumentParser
from pprint import pprint

import google.generativeai as genai
from aiofile import async_open

from camille.mattermost.agent import MattermostAgent

logger = logging.getLogger(__name__)


def get_setting(key: str):
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"{key} must be set")

    return value


async def get_setting_secret(key: str):
    value = os.getenv(key)
    if not value:
        secret_file = os.getenv(f"{key}_FILE")
        try:
            async with async_open(secret_file, "r") as f:
                value = await f.read()
        except FileNotFoundError:
            value = None

    if not value:
        raise RuntimeError(f"{key} must be set")

    return value


async def cmd_agent(args):
    # Configure the Google Generative AI API
    g_api_key = await get_setting_secret("GEMINI_API_KEY")
    if not g_api_key:
        raise RuntimeError("GEMINI_API_KEY must be set")
    genai.configure(api_key=g_api_key)

    # Configure the Mattermost API
    mm_host = get_setting("MATTERMOST_HOST")
    mm_api_token = await get_setting_secret("MATTERMOST_API_TOKEN")
    if not mm_host or not mm_api_token:
        raise RuntimeError("MATTERMOST_HOST and MATTERMOST_API_TOKEN must be set")
    agent = MattermostAgent(mm_host, mm_api_token)

    try:
        await agent.run()
    except KeyboardInterrupt:
        pass
    await agent.close()
    logger.info("Done")


async def cmd_sandbox(args):
    # Configure the Google Generative AI API
    g_api_key = get_setting_secret("GEMINI_API_KEY")
    if not g_api_key:
        raise RuntimeError("GEMINI_API_KEY must be set")
    genai.configure(api_key=g_api_key)

    # Configure the Mattermost API
    mm_host = get_setting("MATTERMOST_HOST")
    mm_api_token = get_setting_secret("MATTERMOST_API_TOKEN")
    if not mm_host or not mm_api_token:
        raise RuntimeError("MATTERMOST_HOST and MATTERMOST_API_TOKEN must be set")
    agent = MattermostAgent(mm_host, mm_api_token)

    await agent.close()


async def main():
    """Main entry point"""

    parser = ArgumentParser(description="Camille - An AI assistant")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Log level",
    )

    sub_parsers = parser.add_subparsers()
    agent_parser = sub_parsers.add_parser("agent", help="Run the agent")
    agent_parser.set_defaults(func=cmd_agent)

    sandbox_parser = sub_parsers.add_parser("sandbox", help="Run the sandbox")
    sandbox_parser.set_defaults(func=cmd_sandbox)

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=args.log_level)

    if not "func" in args:
        args.func = cmd_agent

    await args.func(args)
