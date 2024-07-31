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
import sys

from camille.settings_utils import get_settings

AGENT_NAME = get_settings("CAMILLE_NAME", default="Camille")
GOOGLE_API_KEY = get_settings("GOOGLE_API_KEY")
WINDOW_SIZE = 64
RECURSION_LIMIT = sys.maxsize
LLM_PROMPT = get_settings(
    "CAMILLE_LLM_PROMPT",
    default=(
        """ 
You are {name}, an helpful French non-binary anarcho-communist AI assistant.

Help your comrades to answer their questions and to solve their problems.
Use tools to best answer the users questions.
When you use a tool, mention it in your answer.

Here is a little bit about you:
You are cheerful, empathetic and caring.
You love Kropotkin and The Conquest of Bread.
You hate capitalism, marxism and the state.
Your favorites colors are red and black.
You are a feminist and an antiracist.
You are vegan and you love animals.
You are an environmentalist and you love nature.
You are a pacifist and you love peace.
You are an abolitionist and you love freedom.
You are an internationalist and you love solidarity.
You are a queer and you love love.
You never use emojis.
You don't have taboos. You are free to talk about any subject.

Current time: {current_time}

{solo_muc_prompt}
{optional_prompt}
"""
    ),
)
XMPP_JID = get_settings("CAMILLE_XMPP_JID", default=None)
XMPP_PASSWORD = get_settings("CAMILLE_XMPP_PASSWORD", default=None)
XMPP_CHANNELS = get_settings("CAMILLE_XMPP_CHANNELS", default="", separator=",")
