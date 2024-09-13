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

from camille.mattermost.agent import MattermostAgent

logger = logging.getLogger(__name__)


async def cmd_agent(args):
    # Configure the Google Generative AI API
    g_api_key = os.getenv("GEMINI_API_KEY")
    if not g_api_key:
        raise RuntimeError("GEMINI_API_KEY must be set")
    genai.configure(api_key=g_api_key)

    # Configure the Mattermost API
    mm_host = os.getenv("MATTERMOST_HOST")
    mm_api_token = os.getenv("MATTERMOST_API_TOKEN")
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
    # Configure the Mattermost API
    mm_host = os.getenv("MATTERMOST_HOST")
    mm_api_token = os.getenv("MATTERMOST_API_TOKEN")
    if not mm_host or not mm_api_token:
        raise RuntimeError("MATTERMOST_HOST and MATTERMOST_API_TOKEN must be set")
    agent = MattermostAgent(mm_host, mm_api_token)

    me_id = "edm15sd3cfnruprwaykwrkdwha"
    channel_id = "1po5133tqiy3mfqbzqe17uajoo"
    r = await agent.api.get_posts(channel_id)
    posts = []
    for pid in reversed(r["order"]):
        p = r["posts"][pid]
        if p.get("deleted_at"):
            continue

        if p["root_id"]:
            continue

        posts.append(p)

    # Gemini doesn't like when first message is from the bot
    while posts and posts[0]["user_id"] == me_id:
        posts.pop(0)

    posts = [
        {
            "user_id": p["user_id"],
            "message": p["message"],
            "created_at": p["create_at"],
        }
        for p in posts
    ]

    pprint(posts)

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
