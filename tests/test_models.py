from uuid import UUID

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from camille.models import (
    Agent,
    AgentPersonality,
    AIImageModel,
    AIModel,
    AIProvider,
    ExaApiKey,
    GoogleAIImageModel,
    GoogleAIModel,
    GoogleAIProvider,
    OpenAIAIProvider,
    OpenAIImageModel,
    OpenAIModel,
    Profile,
    TavilyApiKey,
)

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

    def test_clean_accepts_own_model(self):
        user = make_user()
        provider = GoogleAIProvider.objects.create(user=user, api_key="test")
        profile = user.profile
        profile.default_model = GoogleAIModel.objects.create(
            user=user, provider=provider, name="gemini-3.5-flash-lite"
        )

        profile.full_clean()

    def test_clean_rejects_model_of_another_user(self):
        profile = make_user("alice").profile
        other_user = make_user("bob")
        provider = GoogleAIProvider.objects.create(user=other_user, api_key="test")
        profile.default_model = GoogleAIModel.objects.create(
            user=other_user, provider=provider, name="gemini-3.5-flash-lite"
        )

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

        self.assertEqual(agent.name, "default")
        self.assertIsNone(agent.personality)
        self.assertEqual(agent.uuid.version, 7)

    def test_same_name_is_rejected_for_one_user(self):
        user = make_user()

        Agent.objects.create(user=user, name="Bot")

        with self.assertRaises(IntegrityError):
            Agent.objects.create(user=user, name="Bot")

    def test_same_name_is_allowed_for_different_users(self):
        first = Agent.objects.create(user=make_user("alice"), name="Bot")
        second = Agent.objects.create(user=make_user("bob"), name="Bot")

        self.assertEqual(first.name, second.name)

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

    def test_clean_rejects_model_of_another_user(self):
        owner = make_user("bob")
        provider = GoogleAIProvider.objects.create(user=owner, api_key="test")
        model = GoogleAIModel.objects.create(
            user=owner, provider=provider, name="gemini-3.5-flash-lite"
        )
        agent = Agent(user=make_user("alice"), model=model)

        with self.assertRaises(ValidationError):
            agent.full_clean()

    def test_clean_rejects_exa_api_key_of_another_user(self):
        owner = make_user("bob")
        agent = Agent(
            user=make_user("alice"),
            exa_api_key=ExaApiKey.objects.create(user=owner, key="exa-test"),
        )

        with self.assertRaises(ValidationError):
            agent.full_clean()

    def test_clean_rejects_tavily_api_key_of_another_user(self):
        owner = make_user("bob")
        agent = Agent(
            user=make_user("alice"),
            tavily_api_key=TavilyApiKey.objects.create(user=owner, key="tavily-test"),
        )

        with self.assertRaises(ValidationError):
            agent.full_clean()

    def test_clean_rejects_image_model_of_another_user(self):
        owner = make_user("bob")
        provider = GoogleAIProvider.objects.create(user=owner, api_key="test")
        image_model = GoogleAIImageModel.objects.create(
            user=owner, provider=provider, name="imagen-4.0"
        )
        agent = Agent(user=make_user("alice"), imgen_model=image_model)

        with self.assertRaises(ValidationError):
            agent.full_clean()

    def test_clean_accepts_own_sub_agents(self):
        user = make_user()
        agent = Agent.objects.create(user=user)
        agent.sub_agents.add(Agent.objects.create(user=user, name="Helper"))

        agent.full_clean()

    def test_clean_rejects_sub_agent_of_another_user(self):
        agent = Agent.objects.create(user=make_user("alice"))
        agent.sub_agents.add(Agent.objects.create(user=make_user("bob"), name="Helper"))

        with self.assertRaises(ValidationError):
            agent.full_clean()

    def test_get_model_instance_uses_profile_default(self):
        user = make_user()
        provider = GoogleAIProvider.objects.create(user=user, api_key="test")
        model = GoogleAIModel.objects.create(
            user=user, provider=provider, name="gemini-3.5-flash-lite"
        )
        user.profile.default_model = model
        user.profile.save(update_fields=("default_model",))

        agent = Agent.objects.create(user=user)

        self.assertEqual(agent.get_model_instance().model_name, model.name)

    def test_get_model_instance_requires_a_model(self):
        agent = Agent.objects.create(user=make_user())

        with self.assertRaisesMessage(ValueError, "does not have a model assigned"):
            agent.get_model_instance()

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

        self.assertEqual(personality.name, "default")
        self.assertEqual(personality.template, "You are {agent_name}")
        self.assertEqual(personality.uuid.version, 7)

    def test_same_name_is_rejected_for_one_user(self):
        user = make_user()

        AgentPersonality.objects.create(user=user, name="Calm")

        with self.assertRaises(IntegrityError):
            AgentPersonality.objects.create(user=user, name="Calm")

    def test_deleted_with_user(self):
        user = make_user()
        AgentPersonality.objects.create(user=user)

        user.delete()

        self.assertEqual(AgentPersonality.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)


class AIModelTests(TestCase):
    def test_base_classes_require_get_instance_implementation(self):
        user = make_user()
        provider = AIProvider.objects.create(user=user)
        model = AIModel.objects.create(user=user, provider=provider, name="chat")
        image_model = AIImageModel.objects.create(
            user=user, provider=provider, name="image"
        )

        for obj in (provider, model, image_model):
            with (
                self.subTest(model=type(obj).__name__),
                self.assertRaises(NotImplementedError),
            ):
                obj.get_instance()

    def test_model_rejects_provider_of_another_user(self):
        provider = GoogleAIProvider.objects.create(
            user=make_user("bob"), api_key="test"
        )
        model = AIModel(
            user=make_user("alice"),
            provider=provider,
            name="chat",
        )

        with self.assertRaises(ValidationError):
            model.full_clean()

    def test_image_model_rejects_provider_of_another_user(self):
        provider = GoogleAIProvider.objects.create(
            user=make_user("bob"), api_key="test"
        )
        model = AIImageModel(
            user=make_user("alice"),
            provider=provider,
            name="image",
        )

        with self.assertRaises(ValidationError):
            model.full_clean()

    def test_google_models_require_google_provider(self):
        user = make_user()
        provider = OpenAIAIProvider.objects.create(user=user, api_key="test")

        for model in (
            GoogleAIModel(user=user, provider=provider, name="chat"),
            GoogleAIImageModel(user=user, provider=provider, name="image"),
        ):
            with (
                self.subTest(model=type(model).__name__),
                self.assertRaises(ValidationError),
            ):
                model.full_clean()

    def test_openai_models_require_openai_provider(self):
        user = make_user()
        provider = GoogleAIProvider.objects.create(user=user, api_key="test")

        for model in (
            OpenAIModel(user=user, provider=provider, name="chat"),
            OpenAIImageModel(user=user, provider=provider, name="image"),
        ):
            with (
                self.subTest(model=type(model).__name__),
                self.assertRaises(ValidationError),
            ):
                model.full_clean()

    def test_google_instances_use_stored_configuration(self):
        user = make_user()
        provider = GoogleAIProvider.objects.create(user=user, api_key="test")
        model = GoogleAIModel.objects.create(
            user=user, provider=provider, name="gemini-3.5-flash-lite"
        )
        image_model = GoogleAIImageModel.objects.create(
            user=user, provider=provider, name="imagen-4.0"
        )

        model.full_clean()
        image_model.full_clean()
        self.assertEqual(model.get_instance().model_name, model.name)
        self.assertEqual(image_model.get_instance().model_name, image_model.name)

    def test_openai_instances_use_stored_configuration(self):
        user = make_user()
        provider = OpenAIAIProvider.objects.create(
            user=user,
            api_key="test",
            base_url="https://example.com/v1",
        )
        model = OpenAIModel.objects.create(
            user=user, provider=provider, name="gpt-5-mini"
        )
        image_model = OpenAIImageModel.objects.create(
            user=user, provider=provider, name="gpt-image-1"
        )

        model.full_clean()
        image_model.full_clean()
        self.assertEqual(model.get_instance().model_name, model.name)
        self.assertEqual(image_model.get_instance().model_name, image_model.name)

    def test_string_representations(self):
        user = make_user()
        provider = GoogleAIProvider.objects.create(
            user=user, name="google", api_key="test"
        )
        model = GoogleAIModel.objects.create(
            user=user, provider=provider, name="gemini"
        )
        image_model = GoogleAIImageModel.objects.create(
            user=user, provider=provider, name="imagen"
        )
        exa_key = ExaApiKey.objects.create(user=user, name="exa", key="test")
        tavily_key = TavilyApiKey.objects.create(user=user, name="tavily", key="test")

        self.assertEqual(str(provider), "google")
        self.assertEqual(str(model), "google:gemini")
        self.assertEqual(str(image_model), "google:imagen")
        self.assertEqual(str(exa_key), "exa")
        self.assertEqual(str(tavily_key), "tavily")
