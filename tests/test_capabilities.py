from django.test import TestCase

from camille.capabilities.personality import PersonalityCapability
from camille.models import AgentPersonality

from .helpers import make_user


class PersonalityCapabilityTests(TestCase):
    def test_formats_instructions_with_agent_name(self):
        personality = AgentPersonality.objects.create(
            user=make_user(),
            template="You are {agent_name}, a concise assistant.",
        )

        capability = PersonalityCapability(personality, "Camille")

        self.assertEqual(
            capability.get_instructions(),
            "You are Camille, a concise assistant.",
        )
