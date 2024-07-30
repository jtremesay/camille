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

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from camille.llm.assistant import Assistant
from camille.llm.llm import tools
from camille.llm.state import State
from langchain_django.checkpointer import DjangoSaver


def print_event(event: dict, _printed: set, max_length=1500):
    printed_messages = []
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)
            printed_messages.append(message)

    return printed_messages


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ],
        "current_time": datetime.now(),
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


builder = StateGraph(State)

builder.add_node("assistant", Assistant())
builder.add_edge(START, "assistant")

builder.add_node("tools", create_tool_node_with_fallback(tools))
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

saver = DjangoSaver()
part_1_graph = builder.compile(checkpointer=saver)
