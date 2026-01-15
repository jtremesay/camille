import re
from argparse import ArgumentParser, Namespace

from camille.mattermost.client import Mattermost
from camille.models import (
    AWSBedrockCredentials,
    GoogleGLACredentials,
    InferenceProvider,
    MistralAICredentials,
    MMUser,
)

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


async def cmd_set_aws_creds(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    await AWSBedrockCredentials.objects.aupdate_or_create(
        user=mm_user,
        provider=InferenceProvider.AWS_BEDROCK,
        defaults={
            "bearer_token": args.bearer_token,
            "region": args.region,
        },
    )
    await client.post_message(
        channel_id,
        root_id,
        "AWS Bedrock credentials set successfully.",
    )


async def cmd_set_google_gla_creds(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    await GoogleGLACredentials.objects.aupdate_or_create(
        user=mm_user,
        provider=InferenceProvider.GOOGLE_GLA,
        defaults={
            "api_key": args.api_key,
        },
    )
    await client.post_message(
        channel_id,
        root_id,
        "Google GLA credentials set successfully.",
    )


async def cmd_set_mistral_ai_creds(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    await MistralAICredentials.objects.aupdate_or_create(
        user=mm_user,
        provider=InferenceProvider.MISTRAL_AI,
        defaults={
            "api_key": args.api_key,
        },
    )
    await client.post_message(
        channel_id,
        root_id,
        "Mistral AI credentials set successfully.",
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

    set_aws_creds_parser = subparsers.add_parser(
        "set_aws_creds", help="Set AWS Bedrock credentials"
    )
    set_aws_creds_parser.add_argument(
        "bearer_token", type=str, help="AWS Bedrock Bearer Token"
    )
    set_aws_creds_parser.add_argument("region", type=str, help="AWS Region for Bedrock")
    set_aws_creds_parser.set_defaults(func=cmd_set_aws_creds)

    set_google_gla_creds_parser = subparsers.add_parser(
        "set_google_gla_creds", help="Set Google Generative Language API credentials"
    )
    set_google_gla_creds_parser.add_argument(
        "api_key", type=str, help="Google GLA API Key"
    )
    set_google_gla_creds_parser.set_defaults(func=cmd_set_google_gla_creds)

    set_mistral_ai_creds_parser = subparsers.add_parser(
        "set_mistral_ai_creds", help="Set Mistral AI credentials"
    )
    set_mistral_ai_creds_parser.add_argument(
        "api_key", type=str, help="Mistral AI API Key"
    )
    set_mistral_ai_creds_parser.set_defaults(func=cmd_set_mistral_ai_creds)

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
