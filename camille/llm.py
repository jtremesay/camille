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
from typing import Literal

from django.db import models
from langchain_core.messages import RemoveMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

import camille.settings as camille_settings
from langchain_django.checkpointer import DjangoSaver


class LLMModel(models.TextChoices):
    GEMINI_FLASH = "gemini-1.5-flash-latest", "Gemini Flash"
    GEMINI_PRO = "gemini-1.5-pro-latest", "Gemini Pro"


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


class Config(TypedDict):
    model_name: str
    optional_prompt: str
    current_time: datetime
    is_muc: bool


safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", camille_settings.LLM_PROMPT),
        ("placeholder", "{messages}"),
    ]
).partial(name=camille_settings.AGENT_NAME)

tools = []


llms = {
    m: prompt
    | ChatGoogleGenerativeAI(
        model=m,
        api_key=camille_settings.GOOGLE_API_KEY,
        safety_settings=safety_settings,
    ).bind_tools(tools)
    for m in LLMModel.values
}


def delete_old_messages(state):
    messages = state["messages"]
    if len(messages) > camille_settings.WINDOW_SIZE:
        return {
            "messages": [
                RemoveMessage(id=m.id)
                for m in messages[: -camille_settings.WINDOW_SIZE]
            ]
        }


def should_continue(state: MessagesState) -> Literal["action", "delete_messages"]:
    """Return the next node to execute."""
    messages = state["messages"]

    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "delete_messages"

    # Otherwise if there is, we continue
    return "action"


async def agent(state: MessagesState, config: RunnableConfig) -> MessagesState:
    configuration = config.get("configurable", {})
    messages = state["messages"]

    if configuration.get("is_muc", False):
        solo_muc_prompt = "You are in a multi-user chat."
    else:
        solo_muc_prompt = ""

    llm = llms[configuration["model_name"]]

    response = await llm.ainvoke(
        {
            "messages": messages,
            "optional_prompt": configuration.get("optional_prompt", ""),
            "current_time": datetime.now().strftime("%H:%M:%S, %a %d %B %Y"),
            "solo_muc_prompt": solo_muc_prompt,
        }
    )
    return {"messages": response}


action = ToolNode(tools)

workflow = StateGraph(MessagesState, Config)
workflow.add_node("agent", agent)
workflow.add_node("action", action)
workflow.add_node("delete_messages", delete_old_messages)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

workflow.add_edge("action", "agent")
workflow.add_edge("delete_messages", END)


# Build graph
graph = workflow.compile(checkpointer=DjangoSaver())
