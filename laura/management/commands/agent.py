# LAURA - Language Analysis and Understanding Robot Assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from django.core.management.base import BaseCommand

from laura import settings as laura_settings
from laura.agent import Agent, AIMessage, HumanMessage, Messages, SystemMessage


class Command(BaseCommand):
    help = "agent"

    def add_arguments(self, parser):
        parser.add_argument("--repl", action="store_true")

    def handle(self, *args, **options):
        agent = Agent()

        messages = Messages()
        messages |= SystemMessage("You are Laura, an assistant.")
        messages |= AIMessage("Hello, I am Laura, your assistant.")
        messages |= HumanMessage("Hi Laura, how are you?")
        response = agent.process(laura_settings.LLM_MODEL, messages)
        print(response)

        return

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
            # messages |= SystemMessage(
            #    f"You are {laura_settings.NAME}, an assistant in a chat group. You must decide if the messages are addressed to you or not. Say YES if the message is addressed to you, NO otherwise."
            # )
            messages |= SystemMessage(
                "You are {laura_settings.NAME}, an assistant in a chat group. You must assists the users in the chat group but most of them doesn't need you. Only answer to the messages that are addressed to you. Say NO_RESPONSE if the message is not addressed to you."
            )

            messages |= HumanMessage("I love programming.")
            res = agent.process(laura_settings.LLM_MODEL, messages)
            print(res)
            messages |= res

            messages |= HumanMessage("Et les pommes de terre ")
            res = agent.process(laura_settings.LLM_MODEL, messages)
            print(res)
            messages |= res

            messages |= (HumanMessage("Et toi laura, tu aimes quoi ?"),)
            res = agent.process(laura_settings.LLM_MODEL, messages)
            print(res)
            messages |= res
