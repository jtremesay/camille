from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from camille.agents import Deps, create_agent_for_profile
from camille.models import Profile


class Command(BaseCommand):
    help = "CLI command for Camille management tasks"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--user-id",
            type=int,
            help="Specify the user ID to process",
            default=settings.CAMILLE_USER_ID,
        )
        parser.add_argument(
            "--user-name",
            type=str,
            help="Specify the username to process",
            default=settings.CAMILLE_USER_NAME,
        )

        return super().add_arguments(parser)

    def handle(self, *args, **options):
        if (user_id := options.get("user_id")) is not None:
            try:
                profile = Profile.objects.get(user__id=user_id)
            except Profile.DoesNotExist:
                self.stderr.write(f"No user found with ID: {user_id}")
                return
        elif (user_name := options.get("user_name")) is not None:
            try:
                profile = Profile.objects.get(user__username=user_name)
            except Profile.DoesNotExist:
                self.stderr.write(f"No user found with username: {user_name}")
                return
        else:
            self.stderr.write("No user ID or username provided.")
            return

        self.stdout.write(f"Creating agent for user: {profile.user.username}")

        agent = create_agent_for_profile(profile)
        agent.to_cli_sync(deps=Deps(profile=profile))
