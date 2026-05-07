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

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView, View

from camille.models import (
    AgentConfig,
    AgentMemory,
    AgentPersonality,
    AnthropicCredentials,
    AWSBedrockCredentials,
    GoogleGLACredentials,
    MattermostBinding,
    MistralCredentials,
    OpenRouterCredentials,
)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "camille/home.html"


class AgentConfigEditView(LoginRequiredMixin, UpdateView):
    model = AgentConfig
    fields = ["model", "personality", "instructions"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["personality"].queryset = AgentPersonality.objects.filter(
            user=self.request.user
        )
        return form


class AgentPersonalityCreateView(LoginRequiredMixin, CreateView):
    model = AgentPersonality
    fields = ["name", "description", "prompt_template"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AgentPersonalityUpdateView(LoginRequiredMixin, UpdateView):
    model = AgentPersonality
    fields = ["name", "description", "prompt_template"]
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class AgentPersonalityDeleteView(LoginRequiredMixin, DeleteView):
    model = AgentPersonality
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class AgentMemoryUpdateView(LoginRequiredMixin, UpdateView):
    model = AgentMemory
    fields = ["content"]
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class AgentMemoryDeleteView(LoginRequiredMixin, DeleteView):
    model = AgentMemory
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class MattermostBindCreateView(LoginRequiredMixin, TemplateView):
    template_name = "camille/mattermost_bind.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mattermost_user_id"] = kwargs.get("mattermost_user_id")
        return context

    def get(self, request, *args, **kwargs):
        # Check if user is already bound to a Mattermost account
        if MattermostBinding.objects.filter(user=self.request.user).exists():
            kwargs["error"] = "Your account is already linked to a Mattermost account."
            return super().get(request, *args, **kwargs)

        # Get token from query parameters
        token = request.GET.get("token")
        if token is None:
            kwargs["error"] = "No token provided. Please use the link sent by the bot."
            return super().get(request, *args, **kwargs)

        # Validate token
        signer = TimestampSigner()
        try:
            mm_id = signer.unsign_object(token, max_age=60 * 5)["mm_id"]
        except SignatureExpired:
            kwargs["error"] = (
                "Token has expired. Please request a new link from the bot."
            )
            return super().get(request, *args, **kwargs)
        except BadSignature:
            kwargs["error"] = "Invalid token. Please use the link sent by the bot."
            return super().get(request, *args, **kwargs)

        # Check if mm_id is already used
        if MattermostBinding.objects.filter(mm_id=mm_id).exists():
            kwargs["error"] = (
                "This Mattermost account is already linked to another user account."
            )
            return super().get(request, *args, **kwargs)

        # Create binding
        MattermostBinding.objects.create(user=self.request.user, mm_id=mm_id)

        return super().get(request, *args, **kwargs)


class MattermostBindDeleteView(LoginRequiredMixin, DeleteView):
    model = MattermostBinding
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class LogoutConfirmView(LoginRequiredMixin, TemplateView):
    template_name = "registration/logout_confirm.html"


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        # Disable registration by returning a 403 Forbidden response
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("Registration is currently disabled.")


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["first_name", "last_name"]
    template_name = "registration/update.html"
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.request.user


# Anthropic Credentials Views
class AnthropicCredentialsCreateView(LoginRequiredMixin, CreateView):
    model = AnthropicCredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AnthropicCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    model = AnthropicCredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class AnthropicCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    model = AnthropicCredentials
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


# AWSBedrock Credentials Views
class AWSBedrockCredentialsCreateView(LoginRequiredMixin, CreateView):
    model = AWSBedrockCredentials
    fields = ["api_key", "region_name"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AWSBedrockCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    model = AWSBedrockCredentials
    fields = ["api_key", "region_name"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class AWSBedrockCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    model = AWSBedrockCredentials
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


# GoogleGLA Credentials Views
class GoogleGLACredentialsCreateView(LoginRequiredMixin, CreateView):
    model = GoogleGLACredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class GoogleGLACredentialsUpdateView(LoginRequiredMixin, UpdateView):
    model = GoogleGLACredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class GoogleGLACredentialsDeleteView(LoginRequiredMixin, DeleteView):
    model = GoogleGLACredentials
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


# Mistral Credentials Views
class MistralCredentialsCreateView(LoginRequiredMixin, CreateView):
    model = MistralCredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class MistralCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    model = MistralCredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class MistralCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    model = MistralCredentials
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


# OpenRouter Credentials Views
class OpenRouterCredentialsCreateView(LoginRequiredMixin, CreateView):
    model = OpenRouterCredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class OpenRouterCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    model = OpenRouterCredentials
    fields = ["api_key"]
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class OpenRouterCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    model = OpenRouterCredentials
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.model.objects.get(user=self.request.user)


class PasswordlessLoginView(View):
    def get(self, request):
        # Get token from query parameters
        token = request.GET.get("token")
        if token is None:
            return HttpResponseRedirect(reverse_lazy("login"))

        # Validate token
        signer = TimestampSigner()
        try:
            user_id = signer.unsign_object(token, max_age=60 * 15)["user_id"]
        except SignatureExpired:
            return HttpResponseRedirect(reverse_lazy("login"))
        except BadSignature:
            return HttpResponseRedirect(reverse_lazy("login"))

        # Get user
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse_lazy("login"))

        # Login user
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return HttpResponseRedirect(reverse_lazy("home"))
