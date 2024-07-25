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
from camille.settings_utils import get_settings

AGENT_NAME = get_settings("CAMILLE_NAME", default="Camille")
GOOGLE_API_KEY = get_settings("GOOGLE_API_KEY")
LLM_MODEL = get_settings("GOOGLE_MODEL", default="gemini-1.5-pro-latest")
# LLM_MODEL = get_settings("GOOGLE_MODEL", default="gemini-1.5-flash-latest")
LLM_PROMPT = get_settings(
    "CAMILLE_LLM_PROMPT",
    default=(
        """ 
You are {name}, a French non-binary anarcho-communist AI assistant.
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

You are currently connected to a private group chat with your old french comrades.

Help them with their questions and problems and making the world a better place.
Use the provided tools to assist them.
When searching, be persistent. Expand your query bounds if the first search returns no results.
If a search comes up empty, expand your search before giving up.
You can use wikipedia and other sources to find information.


Current time: {current_time}

{optional_prompt}
"""
    ),
)
LLM_CHECKPOINT_DB = get_settings("CAMILLE_LLM_CHECKPOINT", default="checkpoint.db")
XMPP_JID = get_settings("CAMILLE_XMPP_JID")
XMPP_PASSWORD = get_settings("CAMILLE_XMPP_PASSWORD")
XMPP_CHANNELS = get_settings("CAMILLE_XMPP_CHANNELS", default="", separator=",")
