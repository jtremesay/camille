from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from camille.models import Agent, AgentPersonality, Profile

from .helpers import make_user

MODELS = (Profile, Agent, AgentPersonality)


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", password="password")
        cls.user = make_user("alice")
        cls.personality = AgentPersonality.objects.create(user=cls.user)
        cls.agent = Agent.objects.create(user=cls.user, personality=cls.personality)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_changelist_pages(self):
        for model in MODELS:
            with self.subTest(model=model.__name__):
                url = reverse(f"admin:camille_{model._meta.model_name}_changelist")
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_change_pages(self):
        objects = (self.user.profile, self.agent, self.personality)
        for obj in objects:
            with self.subTest(model=type(obj).__name__):
                url = reverse(
                    f"admin:camille_{obj._meta.model_name}_change", args=[obj.pk]
                )
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_search_by_username(self):
        for model in MODELS:
            with self.subTest(model=model.__name__):
                url = reverse(f"admin:camille_{model._meta.model_name}_changelist")
                response = self.client.get(url, {"q": "alice"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["cl"].result_count, 1)

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(reverse("admin:index"))

        self.assertRedirects(
            response, f"{reverse('admin:login')}?next={reverse('admin:index')}"
        )
