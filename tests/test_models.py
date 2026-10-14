from uuid import UUID

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from camille.models import Agent, AgentPersonality, Profile

from .helpers import make_user


class ProfileTests(TestCase):
    def test_created_with_user(self):
        user = make_user()

        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(user.profile.user, user)

    def test_not_duplicated_when_user_is_saved_again(self):
        user = make_user()

        user.first_name = "Alice"
        user.save()

        self.assertEqual(Profile.objects.count(), 1)

    def test_deleted_with_user(self):
        user = make_user()

        user.delete()

        self.assertEqual(Profile.objects.count(), 0)

    def test_uuid_is_v7(self):
        profile = make_user().profile

        self.assertIsInstance(profile.uuid, UUID)
        self.assertEqual(profile.uuid.version, 7)

    def test_default_agent_is_optional(self):
        profile = make_user().profile

        self.assertIsNone(profile.default_agent)
        profile.full_clean()

    def test_clean_accepts_own_agent(self):
        user = make_user()
        profile = user.profile
        profile.default_agent = Agent.objects.create(user=user)

        profile.full_clean()

    def test_clean_rejects_agent_of_another_user(self):
        profile = make_user("alice").profile
        profile.default_agent = Agent.objects.create(user=make_user("bob"))

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_default_agent_unset_when_agent_deleted(self):
        user = make_user()
        agent = Agent.objects.create(user=user)
        Profile.objects.filter(user=user).update(default_agent=agent)

        agent.delete()

        user.profile.refresh_from_db()
        self.assertIsNone(user.profile.default_agent)


class AgentTests(TestCase):
    def test_defaults(self):
        agent = Agent.objects.create(user=make_user())

        self.assertEqual(agent.name, "Default")
        self.assertEqual(agent.slug, "default")
        self.assertIsNone(agent.personality)
        self.assertEqual(agent.uuid.version, 7)

    def test_slug_is_derived_from_name(self):
        agent = Agent.objects.create(user=make_user(), name="My Fancy Agent")

        self.assertEqual(agent.slug, "my-fancy-agent")

    def test_same_name_gets_distinct_slugs_for_one_user(self):
        user = make_user()

        first = Agent.objects.create(user=user, name="Bot")
        second = Agent.objects.create(user=user, name="Bot")

        self.assertNotEqual(first.slug, second.slug)

    def test_same_name_is_allowed_for_different_users(self):
        first = Agent.objects.create(user=make_user("alice"), name="Bot")
        second = Agent.objects.create(user=make_user("bob"), name="Bot")

        self.assertEqual(first.slug, second.slug)

    def test_deleted_with_user(self):
        user = make_user()
        Agent.objects.create(user=user)

        user.delete()

        self.assertEqual(Agent.objects.count(), 0)

    def test_reverse_relations(self):
        user = make_user()
        agent = Agent.objects.create(user=user)

        self.assertEqual(list(user.agents.all()), [agent])

    def test_clean_accepts_no_personality(self):
        Agent(user=make_user()).full_clean()

    def test_clean_accepts_own_personality(self):
        user = make_user()
        personality = AgentPersonality.objects.create(user=user)

        Agent(user=user, personality=personality).full_clean()

    def test_clean_rejects_personality_of_another_user(self):
        personality = AgentPersonality.objects.create(user=make_user("bob"))
        agent = Agent(user=make_user("alice"), personality=personality)

        with self.assertRaises(ValidationError):
            agent.full_clean()

    def test_personality_unset_when_personality_deleted(self):
        user = make_user()
        personality = AgentPersonality.objects.create(user=user)
        agent = Agent.objects.create(user=user, personality=personality)

        personality.delete()

        agent.refresh_from_db()
        self.assertIsNone(agent.personality)


class AgentPersonalityTests(TestCase):
    def test_defaults(self):
        personality = AgentPersonality.objects.create(user=make_user())

        self.assertEqual(personality.name, "Default")
        self.assertEqual(personality.slug, "default")
        self.assertEqual(personality.template, "You are {agent_name}")
        self.assertEqual(personality.uuid.version, 7)

    def test_slug_is_derived_from_name(self):
        personality = AgentPersonality.objects.create(
            user=make_user(), name="Grumpy Pirate"
        )

        self.assertEqual(personality.slug, "grumpy-pirate")

    def test_same_name_gets_distinct_slugs_for_one_user(self):
        user = make_user()

        first = AgentPersonality.objects.create(user=user, name="Calm")
        second = AgentPersonality.objects.create(user=user, name="Calm")

        self.assertNotEqual(first.slug, second.slug)

    def test_deleted_with_user(self):
        user = make_user()
        AgentPersonality.objects.create(user=user)

        user.delete()

        self.assertEqual(AgentPersonality.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
