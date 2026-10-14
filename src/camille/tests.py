from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from .ai import create_pai_agent
from .models import Agent, Profile


class ProfileModelTest(TestCase):
    def test_profile_creation(self):
        assert User.objects.count() == 0
        assert Profile.objects.count() == 0

        user = User.objects.create_user(username="testuser", password="testpassword")
        Profile.objects.get(user=user)
        assert User.objects.count() == 1
        assert Profile.objects.count() == 1

    def test_default_agent_validation(self):
        user = User.objects.create_user(username="testuser", password="testpassword")
        agent = Agent.objects.create(user=user, name="TestAgent")

        profile = user.profile
        profile.default_agent = agent
        profile.clean()

        other_user = User.objects.create_user(
            username="otheruser", password="otherpassword"
        )
        other_profile = other_user.profile
        other_profile.default_agent = agent
        try:
            other_profile.clean()
        except ValidationError:
            pass


class AgentModelTest(TestCase):
    def test_agent_creation(self):
        assert User.objects.count() == 0
        assert Agent.objects.count() == 0

        user = User.objects.create_user(username="testuser", password="testpassword")
        agent = Agent.objects.create(user=user, name="TestAgent")
        assert User.objects.count() == 1
        assert Agent.objects.count() == 1
        assert agent.slug == "testagent"
        assert agent.name == "TestAgent"


class CreatePAIAgentTest(TestCase):
    def test_create_pai_agent(self):
        user = User.objects.create_user(username="testuser", password="testpassword")
        agent = Agent.objects.create(user=user, name="TestAgent")

        create_pai_agent(agent)
