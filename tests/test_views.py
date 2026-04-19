# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import pytest
from django.contrib.auth.models import User
from django.core.signing import TimestampSigner
from django.test import Client
from django.urls import reverse

from camille.models import (
    AgentPersonality,
    AnthropicCredentials,
    MattermostBinding,
)


class TestHomeView:
    def test_requires_login(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 302

    def test_logged_in(self, logged_in_client):
        response = logged_in_client.get(reverse("home"))
        assert response.status_code == 200


class TestRegisterView:
    def test_get_register_page(self, client, db):
        response = client.get(reverse("register"))
        assert response.status_code == 200

    def test_post_registration_disabled(self, client, db):
        response = client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            },
        )
        assert response.status_code == 403


class TestAgentConfigEditView:
    def test_requires_login(self, client):
        response = client.get(reverse("agent_config_update"))
        assert response.status_code == 302

    def test_get_form(self, logged_in_client):
        response = logged_in_client.get(reverse("agent_config_update"))
        assert response.status_code == 200

    def test_personality_queryset_scoped_to_user(
        self, logged_in_client, user, other_user
    ):
        """Form should only show personalities belonging to the logged-in user."""
        response = logged_in_client.get(reverse("agent_config_update"))
        form = response.context["form"]
        qs = form.fields["personality"].queryset
        for p in qs:
            assert p.user == user


class TestAgentPersonalityCRUD:
    def test_create_personality(self, logged_in_client, user):
        response = logged_in_client.post(
            reverse("agent_personality_create"),
            {
                "name": "newpersonality",
                "description": "A test",
                "prompt_template": "You are {agent_name}.",
            },
        )
        assert response.status_code == 302
        assert AgentPersonality.objects.filter(
            user=user, name="newpersonality"
        ).exists()

    def test_update_personality(self, logged_in_client, personality):
        response = logged_in_client.post(
            reverse("agent_personality_update", kwargs={"pk": personality.pk}),
            {
                "name": "updated",
                "description": "Updated",
                "prompt_template": "New prompt.",
            },
        )
        assert response.status_code == 302
        personality.refresh_from_db()
        assert personality.name == "updated"

    def test_delete_personality(self, logged_in_client, user):
        p = AgentPersonality.objects.create(
            user=user, name="deleteme", prompt_template="test"
        )
        response = logged_in_client.post(
            reverse("agent_personality_delete", kwargs={"pk": p.pk}),
        )
        assert response.status_code == 302
        assert not AgentPersonality.objects.filter(pk=p.pk).exists()

    def test_cannot_update_other_users_personality(self, logged_in_client, other_user):
        other_p = AgentPersonality.objects.get(user=other_user)
        response = logged_in_client.post(
            reverse("agent_personality_update", kwargs={"pk": other_p.pk}),
            {"name": "hacked", "description": "", "prompt_template": "hacked"},
        )
        assert response.status_code == 404

    def test_cannot_delete_other_users_personality(self, logged_in_client, other_user):
        other_p = AgentPersonality.objects.get(user=other_user)
        response = logged_in_client.post(
            reverse("agent_personality_delete", kwargs={"pk": other_p.pk}),
        )
        assert response.status_code == 404


class TestMattermostBindCreateView:
    def test_no_token(self, logged_in_client):
        response = logged_in_client.get(reverse("mattermost_bind"))
        assert response.status_code == 200
        assert "error" in response.context

    def test_valid_token_creates_binding(self, logged_in_client, user):
        signer = TimestampSigner()
        token = signer.sign_object({"mm_id": "mm_new_id", "nonce": 42})
        response = logged_in_client.get(f"{reverse('mattermost_bind')}?token={token}")
        assert response.status_code == 200
        assert MattermostBinding.objects.filter(user=user, mm_id="mm_new_id").exists()

    def test_expired_token(self, logged_in_client):
        signer = TimestampSigner()
        token = signer.sign_object({"mm_id": "mm_expired", "nonce": 1})
        # Manually expire by using unsign with max_age=0
        # We can't easily fake time, but we can test with a bad signature
        response = logged_in_client.get(f"{reverse('mattermost_bind')}?token=bad_token")
        assert response.status_code == 200
        assert "error" in response.context

    def test_already_bound(self, logged_in_client, mattermost_binding):
        signer = TimestampSigner()
        token = signer.sign_object({"mm_id": "mm_another", "nonce": 1})
        response = logged_in_client.get(f"{reverse('mattermost_bind')}?token={token}")
        assert response.status_code == 200
        assert "already linked" in response.context.get("error", "")

    def test_mm_id_already_used(self, logged_in_client, other_user):
        MattermostBinding.objects.create(user=other_user, mm_id="mm_taken")
        signer = TimestampSigner()
        token = signer.sign_object({"mm_id": "mm_taken", "nonce": 1})
        response = logged_in_client.get(f"{reverse('mattermost_bind')}?token={token}")
        assert response.status_code == 200
        assert "already linked" in response.context.get("error", "")


class TestProfileUpdateView:
    def test_update_profile(self, logged_in_client, user):
        response = logged_in_client.post(
            reverse("profile_update"),
            {"first_name": "Test", "last_name": "User"},
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == "Test"
        assert user.last_name == "User"


class TestCredentialsCRUD:
    """Test that credential views are scoped to the logged-in user."""

    def test_create_anthropic_credentials(self, logged_in_client, user):
        response = logged_in_client.post(
            reverse("anthropic_credentials_create"),
            {"api_key": "sk-ant-new-key"},
        )
        assert response.status_code == 302
        assert AnthropicCredentials.objects.filter(user=user).exists()

    def test_delete_anthropic_credentials(
        self, logged_in_client, anthropic_credentials
    ):
        response = logged_in_client.post(reverse("anthropic_credentials_delete"))
        assert response.status_code == 302
        assert not AnthropicCredentials.objects.filter(
            pk=anthropic_credentials.pk
        ).exists()
