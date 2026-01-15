import re
from argparse import ArgumentParser, Namespace

from camille.mattermost.client import Mattermost
from camille.models import MMUser

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


async def cmd_ping(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    await client.post_message(
        channel_id,
        root_id,
        "Pong!",
    )


async def cmd_get_model(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    model = mm_user.model or "not set"
    await client.post_message(
        channel_id,
        root_id,
        f"The current model is: {model}",
    )


async def cmd_set_model(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    mm_user.model = args.model
    await mm_user.asave()
    await client.post_message(
        channel_id,
        root_id,
        f"Model set to: {mm_user.model}",
    )


async def handle_command(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    parser = ArgumentParser(prog="command")
    subparsers = parser.add_subparsers(dest="subcommand")

    ping_parser = subparsers.add_parser("ping", help="Check if the bot is responsive")
    ping_parser.set_defaults(func=cmd_ping)

    get_model_parser = subparsers.add_parser(
        "get_model", help="Get the current AI model used by the agent"
    )
    get_model_parser.set_defaults(func=cmd_get_model)

    set_model_parser = subparsers.add_parser(
        "set_model", help="Set the AI model used by the agent"
    )
    set_model_parser.add_argument("model", type=str, help="The AI model to set")
    set_model_parser.set_defaults(func=cmd_set_model)
    try:
        parsed_args = parser.parse_args(args.split())
    except SystemExit:
        help_message = ansi_escape.sub("", parser.format_help())
        await client.post_message(channel_id, root_id, f"```\n{help_message}\n```")
        return

    if func := getattr(parsed_args, "func", None):
        await func(
            client,
            parsed_args,
            channel_id,
            root_id,
            user_id,
        )
    else:
        help_message = ansi_escape.sub("", parser.format_help())
        await client.post_message(channel_id, root_id, f"```\n{help_message}\n```")
