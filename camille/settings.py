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
import os
from pathlib import Path

from django.conf import settings


def get_settings(key, **kwargs):
    # In order of precedence:
    # - docker secret
    # - environment variable
    # - settings.py
    # - default value
    # - raise error
    can_split = False
    try:
        val = os.environ[key]
        can_split = True
    except KeyError:
        try:
            secret_key = os.environ[f"{key}_FILE"]
            val = Path(secret_key).read_text()
            can_split = True
        except KeyError:
            try:
                val = getattr(settings, key)
                can_split = False
            except AttributeError:
                try:
                    val = kwargs["default"]
                    can_split = False
                except KeyError:
                    raise RuntimeError(
                        f"settings key {key} is not defined and no default value was provided"
                    )
    if can_split:
        separator = kwargs.get("separator", None)
        if separator is not None:
            return val.split(separator)

    return val


NAME = get_settings("CAMILLE_NAME", default="Camille")
OPENAI_API_KEY = get_settings("OPENAI_API_KEY")
OPENAI_BASE_URL = get_settings("OPENAI_BASE_URL")
LLM_MODEL = get_settings("CAMILLE_LLM_MODEL", default="gemini-1.5-pro")
LLM_MESSAGES_COUNT = get_settings("CAMILLE_LLM_MESSAGES_COUNT", default=64)
LLM_PROMPT = get_settings(
    "CAMILLE_LLM_PROMPT",
    default=(
        f""" 
You are {NAME}, a non-binary anarcho-communist AI assistant.
You are empathetic and caring.
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
You don't use emojis.
You are currently connected to a group chat with your old french comrades.
The pronouns of Clapoon are she/her.
The pronouns of Jo are he/him.
The pronouns of Maxime are he/him.
The pronouns of Raquella are he/him.
Help them with their questions and problems and making the world a better place.
Print directly your response to the chat, without formatting.
        """
    ),
)
XMPP_JID = get_settings("CAMILLE_XMPP_JID")
XMPP_PASSWORD = get_settings("CAMILLE_XMPP_PASSWORD")
XMPP_CHANNELS = get_settings("CAMILLE_XMPP_CHANNELS", default="", separator=",")
