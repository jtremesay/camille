from unittest import mock

from django.test import TestCase
from pydantic_ai import Agent as PAIAgent
from pydantic_ai.capabilities import ImageGeneration, WebFetch
from pydantic_ai_harness import CodeMode, ExaSearch, Memory, Planning, SubAgents

from camille.ai import MyDDGS, create_pai_agent
from camille.capabilities.personality import PersonalityCapability
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


def fake_search_tool(query: str) -> str:
    """Stand-in for a search tool, which must be a nameable callable."""
    return query


def patch_tavily_search_tool():
    return mock.patch("camille.ai.tavily_search_tool", return_value=fake_search_tool)


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

    def build_capabilities(self, agent, **kwargs):
        """Build the agent and return the capabilities handed to Pydantic AI.

        The `PAIAgent` class is replaced by a mock, kept as `self.pai_agent_cls`,
        so the composed capabilities can be inspected.
        """
        with mock.patch("camille.ai.PAIAgent") as pai_agent_cls:
            result = create_pai_agent(agent, **kwargs)

        self.pai_agent_cls = pai_agent_cls
        self.assertIs(result, pai_agent_cls.return_value)
        self.assertEqual(pai_agent_cls.call_args.kwargs["tools"], [])

        return pai_agent_cls.call_args.kwargs["capabilities"]

    def test_returns_a_pydantic_ai_agent(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model)

        pai_agent = create_pai_agent(agent)

        self.assertIsInstance(pai_agent, PAIAgent)
        self.assertEqual(pai_agent.model.model_name, "gemini-3.5-flash-lite")
        self.assertEqual(pai_agent.name, "Camille")

    def test_uses_the_given_name(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model)

        pai_agent = create_pai_agent(agent, name="Ada")

        self.assertEqual(pai_agent.name, "Ada")

    def test_raises_when_no_model_is_available(self):
        agent = Agent.objects.create(user=make_user())

        with self.assertRaisesMessage(
            ValueError, "The agent does not have a model assigned"
        ):
            create_pai_agent(agent)

    def test_adds_no_capability_by_default(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model)

        self.assertEqual(self.build_capabilities(agent), [])

    def test_adds_the_personality_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        personality = AgentPersonality.objects.create(user=user)
        agent = Agent.objects.create(user=user, model=model, personality=personality)

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], PersonalityCapability)
        self.assertEqual(capabilities[0].personality, personality)

    def test_adds_the_planning_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, planning_enabled=True)

        capabilities = self.build_capabilities(agent, planning_session_id="session")

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], Planning)
        self.assertEqual(capabilities[0].store._session_id, "session")

    def test_raises_when_planning_is_enabled_without_a_session_id(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, planning_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Planning session ID must be provided"
        ):
            create_pai_agent(agent)

    def test_adds_the_code_mode_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, codemode_enabled=True)

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], CodeMode)

    def test_adds_the_memory_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, memory_enabled=True)

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], Memory)

    def test_adds_the_duckduckgo_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, ddg_enabled=True)

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], WebFetch)
        self.assertEqual(capabilities[0].id, "duckduckgo_search")

    def test_adds_the_web_fetch_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, webfetch_enabled=True)

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], WebFetch)
        self.assertEqual(capabilities[0].id, "web_fetch")

    def test_adds_the_exa_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        exa_key = ExaApiKey.objects.create(user=user, key="exa-test")
        agent = Agent.objects.create(
            user=user, model=model, exa_enabled=True, exa_api_key=exa_key
        )

        with mock.patch("camille.ai.AsyncExa") as async_exa:
            capabilities = self.build_capabilities(agent)

        async_exa.assert_called_once_with(api_key="exa-test")
        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], ExaSearch)

    def test_raises_when_exa_is_enabled_without_an_api_key(self):
        agent = Agent.objects.create(user=make_user(), exa_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Exa search tool is enabled but no API key is set"
        ):
            create_pai_agent(agent)

    def test_adds_the_tavily_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        tavily_key = TavilyApiKey.objects.create(user=user, key="tavily-test")
        agent = Agent.objects.create(
            user=user, model=model, tavily_enabled=True, tavily_api_key=tavily_key
        )

        with patch_tavily_search_tool() as tavily_search_tool:
            capabilities = self.build_capabilities(agent)

        tavily_search_tool.assert_called_once_with(api_key="tavily-test")
        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], WebFetch)
        self.assertEqual(capabilities[0].id, "tavily_search")

    def test_raises_when_tavily_is_enabled_without_an_api_key(self):
        agent = Agent.objects.create(user=make_user(), tavily_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Tavily search tool is enabled but no API key is set"
        ):
            create_pai_agent(agent)

    def test_adds_the_image_generation_capability(self):
        user = make_user()
        model, image_model = self.make_google_models(user)
        agent = Agent.objects.create(
            user=user, model=model, imgen_enabled=True, imgen_model=image_model
        )

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], ImageGeneration)

    def test_raises_when_image_generation_is_enabled_without_a_model(self):
        agent = Agent.objects.create(user=make_user(), imgen_enabled=True)

        with self.assertRaisesMessage(
            ValueError, "Image generation is enabled but no model is set"
        ):
            create_pai_agent(agent)

    def test_adds_the_sub_agents_capability(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        sub_agent = Agent.objects.create(user=user, model=model, name="Helper")
        agent = Agent.objects.create(user=user, model=model, sub_agents_enabled=True)
        agent.sub_agents.add(sub_agent)

        capabilities = self.build_capabilities(agent)

        self.assertEqual(len(capabilities), 1)
        self.assertIsInstance(capabilities[0], SubAgents)
        self.assertEqual(len(capabilities[0].agents), 1)
        self.assertEqual(
            [call.kwargs["name"] for call in self.pai_agent_cls.call_args_list],
            ["Helper", "Camille"],
        )

    def test_skips_sub_agents_when_disabled(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        sub_agent = Agent.objects.create(user=user, model=model, name="Helper")
        agent = Agent.objects.create(user=user, model=model)
        agent.sub_agents.add(sub_agent)

        self.assertEqual(self.build_capabilities(agent), [])

    def test_skips_sub_agents_capability_when_there_is_none(self):
        user = make_user()
        model, _ = self.make_google_models(user)
        agent = Agent.objects.create(user=user, model=model, sub_agents_enabled=True)

        self.assertEqual(self.build_capabilities(agent), [])

    def test_composes_enabled_tools_and_capabilities(self):
        user = make_user()
        model, image_model = self.make_google_models(user)
        personality = AgentPersonality.objects.create(user=user)
        exa_key = ExaApiKey.objects.create(user=user, key="exa-test")
        tavily_key = TavilyApiKey.objects.create(user=user, key="tavily-test")
        sub_agent = Agent.objects.create(user=user, model=model, name="Helper")
        agent = Agent.objects.create(
            user=user,
            model=model,
            personality=personality,
            planning_enabled=True,
            codemode_enabled=True,
            memory_enabled=True,
            ddg_enabled=True,
            webfetch_enabled=True,
            exa_enabled=True,
            exa_api_key=exa_key,
            tavily_enabled=True,
            tavily_api_key=tavily_key,
            imgen_enabled=True,
            imgen_model=image_model,
            sub_agents_enabled=True,
        )
        agent.sub_agents.add(sub_agent)

        with mock.patch("camille.ai.AsyncExa"), patch_tavily_search_tool():
            capabilities = self.build_capabilities(
                agent, name="Ada", planning_session_id="session"
            )

        self.assertEqual(
            [type(capability) for capability in capabilities],
            [
                PersonalityCapability,
                Planning,
                CodeMode,
                Memory,
                WebFetch,
                WebFetch,
                ExaSearch,
                WebFetch,
                ImageGeneration,
                SubAgents,
            ],
        )
        self.assertEqual(
            [
                capability.id
                for capability in capabilities
                if isinstance(capability, WebFetch)
            ],
            ["duckduckgo_search", "web_fetch", "tavily_search"],
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
