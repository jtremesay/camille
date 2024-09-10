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

from django.db import models
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain_ollama import ChatOllama

import camille.settings as camille_settings


class LLMModel(models.TextChoices):
    GEMINI_FLASH = "gemini-1.5-flash-latest", "Gemini Flash"
    GEMINI_PRO = "gemini-1.5-pro-latest", "Gemini Pro"

    # Disable non-gemini models
    # (my prod env doesn't have the resources to run them)
    # GEMMA2 = "gemma2", "Gemma 2"


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


def build_llm(llm_model: LLMModel):
    if llm_model == LLMModel.GEMINI_FLASH:
        return ChatGoogleGenerativeAI(
            model=llm_model,
            api_key=camille_settings.GOOGLE_API_KEY,
            safety_settings=safety_settings,
        )
    elif llm_model == LLMModel.GEMINI_PRO:
        return ChatGoogleGenerativeAI(
            model=llm_model,
            api_key=camille_settings.GOOGLE_API_KEY,
            safety_settings=safety_settings,
        )
    else:
        return ChatOllama(model=llm_model)


llms = {m: prompt | build_llm(m) for m in LLMModel.values}


def get_llm(llm_model: LLMModel):
    return llms[llm_model]
