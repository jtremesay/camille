from types import SimpleNamespace

from django.test import TestCase

from camille.capabilities.personality import PersonalityCapability
from camille.models import AgentPersonality

from .helpers import make_user


def make_run_context(agent_name: str) -> SimpleNamespace:
    return SimpleNamespace(agent=SimpleNamespace(name=agent_name))


class PersonalityCapabilityTests(TestCase):
    def test_formats_instructions_with_agent_name(self):
        personality = AgentPersonality.objects.create(
            user=make_user(),
            template="You are {agent_name}, a concise assistant.",
        )

        capability = PersonalityCapability(personality=personality)
        instructions = capability.get_instructions()

        self.assertEqual(
            instructions(make_run_context("Camille")),
            "You are Camille, a concise assistant.",
        )

    def test_keeps_the_personality_it_was_built_with(self):
        personality = AgentPersonality.objects.create(user=make_user())

        capability = PersonalityCapability(personality=personality)

        self.assertIs(capability.personality, personality)

    def test_uses_the_name_of_the_running_agent(self):
        personality = AgentPersonality.objects.create(user=make_user())

        instructions = PersonalityCapability(personality=personality).get_instructions()

        self.assertEqual(instructions(make_run_context("Ada")), "You are Ada")

    def test_supports_templates_without_placeholder(self):
        personality = AgentPersonality.objects.create(
            user=make_user(), template="Answer in French."
        )

        instructions = PersonalityCapability(personality=personality).get_instructions()

        self.assertEqual(instructions(make_run_context("Camille")), "Answer in French.")
