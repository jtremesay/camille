from django.core.management.base import BaseCommand

from laura import settings as laura_settings
from laura.agent import Agent, HumanMessage, Messages


class Command(BaseCommand):
    help = "agent"

    def add_arguments(self, parser):
        parser.add_argument("--repl", action="store_true")

    def handle(self, *args, **options):
        agent = Agent()

        messages = Messages()
        if options["repl"]:
            while True:
                message = input("You: ")
                if message == "exit":
                    break
                messages |= HumanMessage(message)
                res = agent.process(laura_settings.LLM_MODEL, messages)
                print(res)
                messages |= res
        else:
            messages |= HumanMessage("I love programming.")
            res = agent.process(laura_settings.LLM_MODEL, messages)
            print(res)
