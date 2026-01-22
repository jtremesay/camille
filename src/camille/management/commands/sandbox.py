from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from camille.ai.agents import create_agent_for_profile
from camille.ai.deps import Deps
from camille.models import LLMInteraction, LLMThread, Profile


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
        parser.add_argument(
            "-n--new-thread",
            action="store_true",
            help="Create a new LLM thread for the interaction",
        )
        parser.add_argument(
            "-t",
            "--thread-id",
            type=int,
            help="Specify an existing LLM thread ID to continue",
            default=None,
        )

        return super().add_arguments(parser)

    def handle(self, *args, **options):
        profile_qs = Profile.objects.select_related("user")
        if (user_id := options.get("user_id")) is not None:
            profile_qs = profile_qs.filter(user__id=user_id)
        elif (user_name := options.get("user_name")) is not None:
            profile_qs = profile_qs.filter(user__username=user_name)
        else:
            self.stderr.write("No user ID or username provided.")
            return

        profile = profile_qs.first()
        if not profile:
            self.stderr.write("No matching user found.")
            return

        self.stdout.write(
            f"Found user: {profile.user.username} (ID: {profile.user.id})"
        )

        thread = None
        if options.get("new_thread"):
            thread = LLMThread.objects.create()
        elif (thread_id := options.get("thread_id")) is not None:
            thread = LLMThread.objects.filter(
                id=thread_id, interaction__initiator=profile
            ).first()
            if not thread:
                self.stderr.write(
                    f"No thread found with ID {thread_id} for user {profile.user.username}."
                )
                return
            self.stdout.write(f"Continuing existing thread ID {thread.id}.")
        else:
            thread = (
                LLMThread.objects.filter(
                    interaction__initiator=profile,
                )
                .order_by("-created_at")
                .first()
            )
            if not thread:
                thread = LLMThread.objects.create()
                self.stdout.write(f"Created new thread ID {thread.id}.")
            else:
                self.stdout.write(f"Continuing existing thread ID {thread.id}.")

        messages = thread.messages()
        try:
            while True:
                user_input = input("You: ")

                # Recreate the agent for each interaction to ensure fresh state
                profile.refresh_from_db()
                deps = Deps(profile=profile, thread=thread)
                agent = create_agent_for_profile(profile)

                r = agent.run_sync(user_input, deps=deps, message_history=messages)
                LLMInteraction.objects.create(
                    thread=thread,
                    initiator=profile,
                    messages_json=r.new_messages_json(),
                )
                messages.extend(r.new_messages())
                print(r.output)

        except Exception as e:
            # Clean up the thread if no interactions were recorded
            if not thread.interactions.exists():
                self.stdout.write("No interactions recorded; deleting empty thread.")
                thread.delete()

            if isinstance(e, (KeyboardInterrupt, EOFError)):
                self.stdout.write("\nExiting sandbox.")
            else:
                raise e
