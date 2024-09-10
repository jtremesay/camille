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
import asyncio

from django.core.management.base import BaseCommand

import camille.settings as camille_settings
from camille.agent.mattermost import MattermostAgent


class Command(BaseCommand):
    help = "The Mattermost agent for Camille."

    async def arun(self):
        agent = MattermostAgent(
            camille_settings.MATTERMOST_HOST,
            camille_settings.MATTERMOST_API_TOKEN,
            name=camille_settings.AGENT_NAME,
            window_size=camille_settings.WINDOW_SIZE,
        )
        await agent.arun()

    def handle(self, *args, **options):
        asyncio.run(self.arun())
