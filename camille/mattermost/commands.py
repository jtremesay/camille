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


async def cmd_set_prompt(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    mm_user.prompt = args.prompt
    await mm_user.asave()
    await client.post_message(
        channel_id,
        root_id,
        "Custom prompt set successfully.",
    )


async def cmd_get_prompt(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    mm_user = await MMUser.objects.aget(id=user_id)
    prompt = mm_user.prompt or "not set"
    await client.post_message(
        channel_id,
        root_id,
        f"The current custom prompt is:\n{prompt}",
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


async def cmd_tldr(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    await client.post_message(
        channel_id,
        root_id,
        """\
TL;DR:

```
!/set_model google-gla:gemini-flash-latest
!/set_google_gla_creds YOUR_GOOGLE_API_KEY
```

**You must set a model and probably credentials before using Camille.**

Use the following commands to set them:

- `!/set_model <model_name>`: Set the AI model to use.
- `!/set_aws_creds <bearer_token> <region>`: Set AWS Bedrock credentials.
- `!/set_google_gla_creds <api_key>`: Set Google Generative Language API credentials.
- `!/set_mistral_ai_creds <api_key>`: Set Mistral AI credentials.

See [here](https://ai.pydantic.dev/models/overview/) for available models and more information on setting up credentials.

Supported providers:

- [AWS Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [Google GLA](https://ai.google.dev/gemini-api/docs/pricing)
- [Mistral AI](https://docs.mistral.ai/getting-started/models)

Know to work models:

- `bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- `google-gla:gemini-flash-latest`
- `mistral:mistral-medium-latest`

How to get credentials ?

- **AWS Bedrock**: Follow the [AWS Bedrock Getting Started Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html) to create an AWS account and obtain your Bearer Token.
- **Google GLA**: Create an API key [here](https://aistudio.google.com/api-keys).
- **Mistral AI**: Create an API key [here](https://console.mistral.ai/home?workspace_dialog=apiKeys).
""",
    )


async def handle_command(
    client: Mattermost, args: Namespace, channel_id: str, root_id: str, user_id: str
):
    parser = ArgumentParser(prog="command")
    subparsers = parser.add_subparsers(dest="subcommand")

    ping_parser = subparsers.add_parser("ping", help="Check if the bot is responsive")
    ping_parser.set_defaults(func=cmd_ping)

    get_prompt_parser = subparsers.add_parser(
        "get_prompt", help="Get the current custom prompt for the user"
    )
    get_prompt_parser.set_defaults(func=cmd_get_prompt)

    set_prompt_parser = subparsers.add_parser(
        "set_prompt", help="Set a custom prompt for the user"
    )
    set_prompt_parser.add_argument("prompt", type=str, help="The custom prompt to set")
    set_prompt_parser.set_defaults(func=cmd_set_prompt)

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

    tldr_parser = subparsers.add_parser("tldr", help="tl;dr")
    tldr_parser.set_defaults(func=cmd_tldr)

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
