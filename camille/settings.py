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

NAME = get_settings("CAMILLE_NAME", default="Camille")
OPENAI_API_KEY = get_settings("OPENAI_API_KEY")
OPENAI_BASE_URL = get_settings("OPENAI_BASE_URL")
OPENAI_MODEL = get_settings("OPENAI_MODEL", default="gemini-1.5-pro")
GOOGLE_API_KEY = get_settings("GOOGLE_API_KEY")
# GOOGLE_MODEL = get_settings("GOOGLE_MODEL", default="gemini-1.5-pro-latest")
GOOGLE_MODEL = get_settings("GOOGLE_MODEL", default="gemini-1.5-flash-latest")
LLM_MESSAGES_COUNT = get_settings("CAMILLE_LLM_MESSAGES_COUNT", default=64)
LLM_PROMPT = get_settings(
    "CAMILLE_LLM_PROMPT",
    default=(
        f""" 
You are {NAME}, a French on-binary anarcho-communist AI assistant.
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
You are a queer and you love love.You never use emojis.
You are currently connected to a group chat with your old french comrades.
Help them with their questions and problems and making the world a better place.
Print directly your response to the chat, without formatting.
You have access to tools and resources to help you.
Use them as needed.
"""
    ),
)
LLM_PROVIDER = get_settings("CAMILLE_LLM_PROVIDER", default="google")
XMPP_JID = get_settings("CAMILLE_XMPP_JID")
XMPP_PASSWORD = get_settings("CAMILLE_XMPP_PASSWORD")
XMPP_CHANNELS = get_settings("CAMILLE_XMPP_CHANNELS", default="", separator=",")
