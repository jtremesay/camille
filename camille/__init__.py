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

import google.generativeai as genai

from camille.mattermost.agent import MattermostAgent

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

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
