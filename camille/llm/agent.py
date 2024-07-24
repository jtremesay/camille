from datetime import datetime

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

import camille.settings as camille_settings
from camille.llm.state import State


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            state = {
                **state,
                "current_time": datetime.now().strftime("%H:%M:%S, %a %d %B %Y"),
                "optional_prompt": configuration.get("optional_prompt", ""),
            }
            if buffered_messages := configuration.get("buffered_messages", []):
                last_message = state["messages"].pop()
                state = {
                    **state,
                    "messages": state["messages"] + buffered_messages + [last_message],
                }
                configuration["buffered_messages"] = []

            result = self.runnable.invoke(state)
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


llm = ChatGoogleGenerativeAI(model=camille_settings.LLM_MODEL)

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", camille_settings.LLM_PROMPT),
        ("placeholder", "{messages}"),
    ]
).partial(name=camille_settings.AGENT_NAME)

part_1_tools = [
    WikipediaQueryRun(
        name=f"wikipedia_{lc}",
        description=(
            f"A wrapper around the {l} version of Wikipedia. "
            "Useful for when you need to answer general questions about "
            "people, places, companies, facts, historical events, or other subjects. "
            "Input should be a search query."
        ),
        api_wrapper=WikipediaAPIWrapper(lang=lc),
    )
    for (lc, l) in [("en", "English"), ("fr", "French")]
]


part_1_assistant_runnable = primary_assistant_prompt | llm.bind_tools(part_1_tools)
