from django.conf import settings
from httpx import Client


class HtttPClient(Client):
    def __init__(self, *args, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["User-Agent"] = settings.CAMILLE_USER_AGENT
        super().__init__(*args, headers=headers, **kwargs)
