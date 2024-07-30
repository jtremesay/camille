# Camille - An AI assistant
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
from datetime import datetime

from langchain_core.runnables import RunnableConfig

from camille.llm.llm import available_llms, default_llm
from camille.llm.state import State


def filter_messages(messages: list[str]) -> list[str]:
    messages = messages[-63:]
    while messages and messages[0].type != "human":
        messages.pop(0)

    return messages


class Assistant:
    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            state = {
                **state,
                "current_time": datetime.now().strftime("%H:%M:%S, %a %d %B %Y"),
                "optional_prompt": configuration.get("optional_prompt", ""),
            }

            if configuration.get("is_muc", False):
                state["solo_muc_prompt"] = "You are in a multi-user chat."
            else:
                state["solo_muc_prompt"] = ""

            if buffered_messages := configuration.get("buffered_messages", []):
                last_message = state["messages"].pop()
                state = {
                    **state,
                    "messages": state["messages"] + buffered_messages + [last_message],
                }
                configuration["buffered_messages"] = []

            state["messages"] = filter_messages(state["messages"])

            try:
                llm = available_llms[configuration["model"]]
            except KeyError:
                llm = default_llm
            result = llm.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
