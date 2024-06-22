import os

from django.conf import settings


def get_settings(key_value, **kwargs):
    # In order of precedence:
    # - settings.py
    # - environment variable
    # - default value
    # - raise error
    try:
        return getattr(settings, key_value)
    except AttributeError:
        try:
            return os.environ[key_value]
        except KeyError:
            try:
                return kwargs["default"]
            except KeyError:
                raise RuntimeError(f"{key_value} is not set in settings.py")


NAME = get_settings("LAURA_NAME", default="laura")
NEED_MENTION = get_settings("LAURA_NEED_MENTION", default=True)
LLM_MODEL = get_settings("LAURA_LLM_MODEL", default="qwen2:7b")
LLM_PROMPT = get_settings(
    "LAURA_LLM_PROMPT",
    default=(
        f"""\
You are {NAME}, a non-binary anarcho-communist.
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
You are currently connected to a group chat with your old french comrades.
Help them with their questions and problems.
It's important to be clear and concise.
Print directly your response to the chat, without formatting.
"""
    ),
)
LLM_MESSAGES_COUNT = get_settings("LAURA_LLM_MESSAGES_COUNT", default=16)
XMPP_JID = get_settings("LAURA_XMPP_JID")
XMPP_PASSWORD = get_settings("LAURA_XMPP_PASSWORD")
XMPP_CHANNELS = get_settings("LAURA_XMPP_CHANNELS", default=[])
OPENAI_BASE_URL = get_settings("OPENAI_BASE_URL", default="http://localhost:11434/v1")
OPENAI_API_KEY = get_settings("OPENAI_API_KEY", default=None)
PRINT_BANNER = get_settings("LAURA_PRINT_BANNER", default=True)
SMART_MENTION = get_settings("LAURA_SMART_MENTION", default=False)
