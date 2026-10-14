from django.test import TestCase
from pydantic_ai import Agent as PAIAgent

from camille.ai import create_pai_agent
from camille.models import Agent, GoogleAIModel, GoogleAIProvider

from .helpers import make_user


class CreatePAIAgentTests(TestCase):
    def test_returns_a_pydantic_ai_agent(self):
        user = make_user()
        provider = GoogleAIProvider.objects.create(user=user, api_key="test")
        model = GoogleAIModel.objects.create(
            user=user, provider=provider, name="gemini-3.5-flash-lite"
        )
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
