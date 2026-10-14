from unittest import mock

from django.test import TestCase
from pydantic_ai import Agent as PAIAgent

from camille.ai import MyDDGS, create_pai_agent
from camille.models import (
    Agent,
    AgentPersonality,
    ExaApiKey,
    GoogleAIImageModel,
    GoogleAIModel,
    GoogleAIProvider,
    TavilyApiKey,
)

from .helpers import make_user


class CreatePAIAgentTests(TestCase):
    def make_google_models(self, user):
        provider = GoogleAIProvider.objects.create(user=user, api_key="test")
        model = GoogleAIModel.objects.create(
            user=user, provider=provider, name="gemini-3.5-flash-lite"
        )
        image_model = GoogleAIImageModel.objects.create(
            user=user, provider=provider, name="imagen-4.0"
        )
        return model, image_model

    def test_returns_a_pydantic_ai_agent(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model)

        pai_agent = create_pai_agent(agent)

        self.assertIsInstance(pai_agent, PAIAgent)
        self.assertEqual(pai_agent.model.model_name, "gemini-3.5-flash-lite")

    def test_raises_when_image_generation_is_enabled_without_a_model(self):
        agent = Agent.objects.create(user=make_user(), imgen_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Image generation is enabled but no model is set"
        ):
            create_pai_agent(agent)

    def test_raises_when_exa_is_enabled_without_an_api_key(self):
        agent = Agent.objects.create(user=make_user(), exa_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Exa search tool is enabled but no API key is set"
        ):
            create_pai_agent(agent)

    def test_raises_when_tavily_is_enabled_without_an_api_key(self):
        agent = Agent.objects.create(user=make_user(), tavily_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Tavily search tool is enabled but no API key is set"
        ):
            create_pai_agent(agent)

    def test_composes_enabled_tools_and_capabilities(self):
        user = make_user()
        model, image_model = self.make_google_models(user)
        personality = AgentPersonality.objects.create(user=user)
        exa_key = ExaApiKey.objects.create(user=user, key="exa-test")
        tavily_key = TavilyApiKey.objects.create(user=user, key="tavily-test")
        agent = Agent.objects.create(
            user=user,
            model=model,
            personality=personality,
            ddg_enabled=True,
            webfetch_enabled=True,
            exa_enabled=True,
            exa_api_key=exa_key,
            tavily_enabled=True,
            tavily_api_key=tavily_key,
            imgen_enabled=True,
            imgen_model=image_model,
        )

        with mock.patch.multiple(
            "camille.ai",
            duckduckgo_search_tool=mock.DEFAULT,
            web_fetch_tool=mock.DEFAULT,
            AsyncExa=mock.DEFAULT,
            ExaSearch=mock.DEFAULT,
            tavily_search_tool=mock.DEFAULT,
            ImageGenerator=mock.DEFAULT,
            ImageGeneration=mock.DEFAULT,
            PAIAgent=mock.DEFAULT,
        ) as patched:
            result = create_pai_agent(agent, name="Ada")

        self.assertIs(result, patched["PAIAgent"].return_value)
        patched["AsyncExa"].assert_called_once_with(api_key="exa-test")
        patched["tavily_search_tool"].assert_called_once_with(api_key="tavily-test")
        patched["ImageGenerator"].assert_called_once()
        patched["PAIAgent"].assert_called_once_with(
            model=mock.ANY,
            tools=[
                patched["duckduckgo_search_tool"].return_value,
                patched["web_fetch_tool"].return_value,
                patched["tavily_search_tool"].return_value,
            ],
            capabilities=[
                mock.ANY,
                patched["ExaSearch"].return_value,
                patched["ImageGeneration"].return_value,
            ],
        )


class MyDDGSTests(TestCase):
    @mock.patch("camille.ai.DDGS._search_sync")
    def test_delegates_search(self, search_sync):
        search_sync.return_value = [{"title": "result"}]

        self.assertEqual(MyDDGS()._search_sync("query"), [{"title": "result"}])

    @mock.patch("camille.ai.DDGS._search_sync")
    def test_returns_no_results_when_search_fails(self, search_sync):
        from ddgs.ddgs import DDGSException

        search_sync.side_effect = DDGSException("unavailable")

        with self.assertLogs("camille.ai", level="ERROR"):
            results = MyDDGS()._search_sync("query")

        self.assertEqual(results, [])
