from os import environ
from unittest import mock

from django.test import TestCase
from pydantic_ai import Agent as PAIAgent

from camille.ai import create_pai_agent
from camille.models import Agent

from .helpers import make_user


class CreatePAIAgentTests(TestCase):
    def test_returns_a_pydantic_ai_agent(self):
        agent = Agent.objects.create(user=make_user())

        with mock.patch.dict(environ, {"GOOGLE_API_KEY": "test"}):
            pai_agent = create_pai_agent(agent)

        self.assertIsInstance(pai_agent, PAIAgent)
        self.assertEqual(pai_agent.model.model_name, "gemini-3.5-flash-lite")
