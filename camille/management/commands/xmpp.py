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
from django.core.management.base import BaseCommand

import camille.settings as camille_settings
from camille.agent.xmpp import XmppAgent


class Command(BaseCommand):
    help = "The XMPP agent for Camille."

    def handle(self, *args, **options):
        agent = XmppAgent(
            jid=camille_settings.XMPP_JID,
            password=camille_settings.XMPP_PASSWORD,
            channels=camille_settings.XMPP_CHANNELS,
            name=camille_settings.AGENT_NAME,
            window_size=camille_settings.WINDOW_SIZE,
        )
        agent.run()
