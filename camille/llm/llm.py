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
from django.db import models
from langchain_community.tools import WikipediaQueryRun
from langchain_community.tools.openweathermap.tool import OpenWeatherMapQueryRun
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import OpenWeatherMapAPIWrapper, WikipediaAPIWrapper
from langchain_community.utilities.requests import GenericRequestsWrapper
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)

import camille.settings as camille_settings
from camille.llm.tools import RequestsGetInput


class LLMModel(models.TextChoices):
    GEMINI_FLASH = "gemini-1.5-flash-latest", "Gemini Flash"
    GEMINI_PRO = "gemini-1.5-pro-latest", "Gemini Pro"


primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", camille_settings.LLM_PROMPT),
        ("placeholder", "{messages}"),
    ]
).partial(name=camille_settings.AGENT_NAME)

tools = [
    RequestsGetTool(
        requests_wrapper=GenericRequestsWrapper(),
        allow_dangerous_requests=True,
        args_schema=RequestsGetInput,
    ),
    TavilySearchResults(
        api_wrapper=TavilySearchAPIWrapper(
            tavily_api_key=camille_settings.TAVILY_API_KEY
        ),
        description="""A search engine optimized for comprehensive, accurate, \
and trusted results. Useful for when you need to answer questions \
about current events or about recent information. \
Input should be a search query. \
If the user is asking about something that you don't know about, \
you should probably use this tool to see if that can provide any information.""",
    ),
    OpenWeatherMapQueryRun(
        api_wrapper=OpenWeatherMapAPIWrapper(
            openweathermap_api_key=camille_settings.OPENWEATHERMAP_API_KEY
        )
    ),
]
tools += [
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


available_llms = {
    m: primary_assistant_prompt
    | ChatGoogleGenerativeAI(
        model=m,
        api_key=camille_settings.GOOGLE_API_KEY,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    ).bind_tools(tools)
    for m in LLMModel
}
default_llm = available_llms[LLMModel.GEMINI_FLASH]
