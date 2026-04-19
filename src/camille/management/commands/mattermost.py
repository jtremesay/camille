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

from asyncio import run

from django.core.management.base import BaseCommand

from camille.mattermost import Mattermost


class Command(BaseCommand):
    help = "Mattermost agent"

    def handle(self, *args, **options):
        run(self.ahandle(*args, **options))

    async def ahandle(self, *args, **options):
        async with Mattermost() as mm:
            await mm.run()
