from argparse import ArgumentParser
from os import environ

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from camille.models import (
    AnthropicCredentials,
    AWSBedrockCredentials,
    GatewayCredentials,
    GoogleGLACredentials,
    MistralCredentials,
    OpenRouterCredentials,
)


class Command(BaseCommand):
    help = "Mattermost agent"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("username")

    def handle(self, *args, username: str, **options):
        user = User.objects.get(username=username)

        if api_key := environ.get("ANTHROPIC_API_KEY"):
            AnthropicCredentials.objects.update_or_create(
                user=user,
                defaults={
                    "api_key": api_key,
                },
            )
            self.stdout.write(
                self.style.SUCCESS("Anthropic credentials imported successfully.")
            )

        if api_key := environ.get("AWS_BEARER_TOKEN_BEDROCK"):
            AWSBedrockCredentials.objects.update_or_create(
                user=user,
                defaults={
                    "api_key": api_key,
                    "region": "us-east-1",
                },
            )
            self.stdout.write(
                self.style.SUCCESS("AWS Bedrock credentials imported successfully.")
            )

        if api_key := environ.get("GATEWAY_API_KEY"):
            GatewayCredentials.objects.update_or_create(
                user=user,
                defaults={
                    "api_key": api_key,
                },
            )
            self.stdout.write(
                self.style.SUCCESS("Gateway credentials imported successfully.")
            )

        if api_key := environ.get("GOOGLE_GLA_API_KEY"):
            GoogleGLACredentials.objects.update_or_create(
                user=user,
                defaults={
                    "api_key": api_key,
                },
            )
            self.stdout.write(
                self.style.SUCCESS("Google GLA credentials imported successfully.")
            )

        if api_key := environ.get("MISTRAL_API_KEY"):
            MistralCredentials.objects.update_or_create(
                user=user,
                defaults={
                    "api_key": api_key,
                },
            )
            self.stdout.write(
                self.style.SUCCESS("Mistral credentials imported successfully.")
            )

        if api_key := environ.get("OPENROUTER_API_KEY"):
            OpenRouterCredentials.objects.update_or_create(
                user=user,
                defaults={
                    "api_key": api_key,
                },
            )
            self.stdout.write(
                self.style.SUCCESS("OpenRouter credentials imported successfully.")
            )
