from dataclasses import dataclass
from json import loads as json_loads
from typing import Optional

import logfire
from channels.db import aclose_old_connections

from camille.mattermost.client import Mattermost
from camille.models import MMChannel, MMMembership, MMTeam, MMUser


@dataclass
class Dependency:
    channel: MMChannel
    users: dict[str, MMUser]


class CommandHandler:
    def __init__(self, client: Mattermost):
        self.client = client

    async def handle(
        self, command_line: str, channel_id: str, root_id: str, user_id: str
    ):
        # Simple command parser: split by spaces
        try:
            command, args = command_line.split(" ", 1)
        except ValueError:
            command = command_line
            args = ""

        match command:
            case "ping":
                await self.cmd_ping(args, channel_id, root_id, user_id)
            case "get_model":
                await self.cmd_get_model(args, channel_id, root_id, user_id)
            case "set_model":
                await self.cmd_set_model(args, channel_id, root_id, user_id)
            case _:
                await self.cmd_help(args, channel_id, root_id, user_id)

    async def cmd_help(self, args: str, channel_id: str, root_id: str, user_id: str):
        match args:
            case "ping":
                message = """\
Usage: `!/ping`

Check if the bot is responsive.

Example:

```
!/ping
```
"""
            case "get_model":
                message = """\
Usage: `!/get_model`

Get the current AI model used by the agent.

Example:

```
!/get_model
```
"""
            case "set_model":
                message = """\
Usage: !/set_model <model_name>

Set the AI model to be used by the agent.

See [here](https://developers.generativeai.google/products/gemini/models) for available models.

Known models:

- `bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- `google-gla:gemini-flash-latest`
- `mistral:mistral-medium-latest`

Example:

```
!/set_model google-gla:gemini-flash-latest
```
"""
            case _:
                message = """\
Available commands:
- `!/ping`: Check if the bot is responsive.
- `!/get_model`: Get the current AI model used by the agent.
- `!/set_model <model_name>`: Set the AI model to be used by the agent.

Use `!/help <command>` for detailed usage of a specific command.
"""

        await self.client.post_message(channel_id, root_id, message)

    async def cmd_ping(self, args: str, channel_id: str, root_id: str, user_id: str):
        await self.client.post_message(
            channel_id,
            root_id,
            "Pong!",
        )

    async def cmd_get_model(
        self, args: str, channel_id: str, root_id: str, user_id: str
    ):
        mm_user = await MMUser.objects.aget(id=user_id)
        model = mm_user.model or "not set"
        await self.client.post_message(
            channel_id,
            root_id,
            f"The current model is: {model}",
        )

    async def cmd_set_model(
        self, args: str, channel_id: str, root_id: str, user_id: str
    ):
        if not args:
            return await self.cmd_help("set_model", channel_id, root_id, user_id)

        mm_user = await MMUser.objects.aget(id=user_id)
        mm_user.model = args.strip()
        await mm_user.asave()
        await self.client.post_message(
            channel_id,
            root_id,
            f"Model set to: {mm_user.model}",
        )


class MattermostAgent(Mattermost):
    def __init__(self, base_url: str, token: str):
        super().__init__(base_url, token)
        self.me: Optional[MMUser] = None

    async def connect(self):
        me_data = await self.get_me()
        self.me = (
            await MMUser.objects.aupdate_or_create(
                id=me_data.id,
                defaults={
                    "username": me_data.username,
                    "nickname": me_data.nickname,
                    "first_name": me_data.first_name,
                    "last_name": me_data.last_name,
                },
            )
        )[0]

        await super().connect()

    async def sync_db(self):
        if self.me is None:
            raise RuntimeError("Bot user is not initialized")

        for user_data in await self.get_users():
            await MMUser.objects.aupdate_or_create(
                id=user_data.id,
                defaults={
                    "username": user_data.username,
                    "nickname": user_data.nickname,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                },
            )

        for team_data in await self.get_teams(self.me.id):
            await MMTeam.objects.aupdate_or_create(
                id=team_data.id,
                defaults={
                    "name": team_data.name,
                    "display_name": team_data.display_name,
                },
            )
            for channel_data in await self.get_channels_for_user(
                self.me.id, team_data.id
            ):
                await MMChannel.objects.aupdate_or_create(
                    id=channel_data.id,
                    defaults={
                        "team_id": team_data.id,
                        "type": channel_data.type,
                        "name": channel_data.name,
                        "display_name": channel_data.display_name,
                        "header": channel_data.header,
                        "purpose": channel_data.purpose,
                    },
                )
                for member_data in await self.get_channel_members(channel_data.id):
                    await MMMembership.objects.aupdate_or_create(
                        channel_id=channel_data.id,
                        user_id=member_data.user_id,
                    )

    @logfire.instrument("event {kind=}")
    async def on_event(self, kind: str, data, broadcast, seq):
        await aclose_old_connections()
        await super().on_event(kind, data, broadcast, seq)

    async def on_hello(self, data, broadcast, seq):
        await self.sync_db()

    async def on_posted(self, data, broadcast, seq):
        if self.me is None:
            raise RuntimeError("Bot user is not initialized")

        post = json_loads(data["post"])

        # Ignore posts sent by the bot itself
        sender_id = post["user_id"]
        if sender_id == self.me.id:
            return

        # Ignore messages that are not simple text posts
        if post["type"]:
            return

        channel_type = data["channel_type"]
        channel_id = post["channel_id"]
        post_id = post["id"]
        root_id = post.get("root_id") or post_id
        message = post["message"]

        # Handle commands starting with "!/"
        if message.startswith("!/"):
            command_line = message[2:].strip()
            cli_handler = CommandHandler(self)
            try:
                await cli_handler.handle(command_line, channel_id, root_id, sender_id)
            except Exception as e:
                logfire.error("Error handling command", error=e)
                await self.post_message(
                    channel_id,
                    root_id,
                    f"An error occurred while processing your command:\n°°°{e}°°°",
                )
            return

        print(data)
        print(broadcast)

    async def on_user_added(self, data, broadcast, seq):
        user_id = data["user_id"]
        channel_id = broadcast["channel_id"]

        try:
            await MMUser.objects.aget(id=user_id)
        except MMUser.DoesNotExist:
            user_data = await self.get_user(user_id)
            await MMUser.objects.acreate(
                id=user_id,
                username=user_data.username,
                nickname=user_data.nickname,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
            )

        try:
            await MMChannel.objects.aget(id=channel_id)
        except MMChannel.DoesNotExist:
            channel_data = await self.get_channel(channel_id)
            await MMChannel.objects.acreate(
                id=channel_id,
                team_id=channel_data.team_id,
                type=channel_data.type,
                name=channel_data.name,
                display_name=channel_data.display_name,
                header=channel_data.header,
                purpose=channel_data.purpose,
            )

        await MMMembership.objects.aupdate_or_create(
            channel_id=channel_id,
            user_id=user_id,
        )

    async def on_user_updated(self, data, broadcast, seq):
        user_data = data["user"]
        await MMUser.objects.aupdate_or_create(
            id=user_data["id"],
            defaults={
                "username": user_data["username"],
                "nickname": user_data["nickname"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
            },
        )

    async def on_channel_updated(self, data, broadcast, seq):
        channel_data = json_loads(data["channel"])
        await MMChannel.objects.aupdate_or_create(
            id=channel_data["id"],
            defaults={
                "team_id": channel_data["team_id"],
                "type": channel_data["type"],
                "name": channel_data["name"],
                "display_name": channel_data["display_name"],
                "header": channel_data["header"],
                "purpose": channel_data["purpose"],
            },
        )
