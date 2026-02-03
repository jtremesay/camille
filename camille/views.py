from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .models import (
    AwsBedrockCredentials,
    BaseCredentials,
    GoogleGlaCredentials,
    MistralCredentials,
    UserCredentials,
)


class LandingPageView(TemplateView):
    """Landing page for unauthenticated users."""

    template_name = "camille/landing.html"


class HomeView(LoginRequiredMixin, TemplateView):
    """Home page for authenticated users."""

    template_name = "camille/home.html"


class LogoutConfirmView(LoginRequiredMixin, TemplateView):
    """Logout confirmation page."""

    template_name = "registration/logout_confirm.html"


class CredentialsListView(LoginRequiredMixin, ListView):
    """Dashboard showing all credentials for the current user."""

    model = BaseCredentials
    template_name = "camille/credentials_list.html"
    context_object_name = "user_credentials"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Separate credentials by type
        context["aws_credentials"] = list(
            c
            for c in AwsBedrockCredentials.objects.filter(
                user_credential__user_profile__user=self.request.user
            )
        )
        context["google_credentials"] = list(
            c
            for c in GoogleGlaCredentials.objects.filter(
                user_credential__user_profile__user=self.request.user
            )
        )
        context["mistral_credentials"] = list(
            c
            for c in MistralCredentials.objects.filter(
                user_credential__user_profile__user=self.request.user
            )
        )

        return context


# AWS Bedrock Credentials Views


class AwsBedrockCredentialsCreateView(LoginRequiredMixin, CreateView):
    """Create new AWS Bedrock credentials."""

    model = AwsBedrockCredentials
    template_name = "camille/credential_form.html"
    fields = ["name", "api_key", "region_name"]
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "AWS Bedrock"
        context["action"] = "Add"
        return context

    def form_valid(self, form):
        """Save the credential and link it to the current user's profile."""
        response = super().form_valid(form)
        UserCredentials.objects.create(
            user_profile=self.request.user.profile,
            credentials=self.object,
        )
        return response


class AwsBedrockCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing AWS Bedrock credentials."""

    model = AwsBedrockCredentials
    template_name = "camille/credential_form.html"
    fields = ["name", "api_key", "region_name"]
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "AWS Bedrock"
        context["action"] = "Edit"
        return context

    def get_queryset(self):
        """Only allow editing credentials owned by the current user."""
        return AwsBedrockCredentials.objects.filter(
            user_credential__user_profile=self.request.user.profile
        )


class AwsBedrockCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    """Delete AWS Bedrock credentials."""

    model = AwsBedrockCredentials
    template_name = "camille/credential_confirm_delete.html"
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "AWS Bedrock"
        return context

    def get_queryset(self):
        """Only allow deleting credentials owned by the current user."""
        return AwsBedrockCredentials.objects.filter(
            user_credential__user_profile=self.request.user.profile
        )


# Google GLA Credentials Views


class GoogleGlaCredentialsCreateView(LoginRequiredMixin, CreateView):
    """Create new Google GLA credentials."""

    model = GoogleGlaCredentials
    template_name = "camille/credential_form.html"
    fields = ["name", "api_key"]
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "Google GLA"
        context["action"] = "Add"
        return context

    def form_valid(self, form):
        """Save the credential and link it to the current user's profile."""
        response = super().form_valid(form)
        UserCredentials.objects.create(
            user_profile=self.request.user.profile,
            credentials=self.object,
        )
        return response


class GoogleGlaCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing Google GLA credentials."""

    model = GoogleGlaCredentials
    template_name = "camille/credential_form.html"
    fields = ["name", "api_key"]
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "Google GLA"
        context["action"] = "Edit"
        return context

    def get_queryset(self):
        """Only allow editing credentials owned by the current user."""
        return GoogleGlaCredentials.objects.filter(
            user_credential__user_profile=self.request.user.profile
        )


class GoogleGlaCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    """Delete Google GLA credentials."""

    model = GoogleGlaCredentials
    template_name = "camille/credential_confirm_delete.html"
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "Google GLA"
        return context

    def get_queryset(self):
        """Only allow deleting credentials owned by the current user."""
        return GoogleGlaCredentials.objects.filter(
            user_credential__user_profile=self.request.user.profile
        )


# Mistral Credentials Views


class MistralCredentialsCreateView(LoginRequiredMixin, CreateView):
    """Create new Mistral credentials."""

    model = MistralCredentials
    template_name = "camille/credential_form.html"
    fields = ["name", "api_key"]
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "Mistral"
        context["action"] = "Add"
        return context

    def form_valid(self, form):
        """Save the credential and link it to the current user's profile."""
        response = super().form_valid(form)
        UserCredentials.objects.create(
            user_profile=self.request.user.profile,
            credentials=self.object,
        )
        return response


class MistralCredentialsUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing Mistral credentials."""

    model = MistralCredentials
    template_name = "camille/credential_form.html"
    fields = ["name", "api_key"]
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "Mistral"
        context["action"] = "Edit"
        return context

    def get_queryset(self):
        """Only allow editing credentials owned by the current user."""
        return MistralCredentials.objects.filter(
            user_credential__user_profile=self.request.user.profile
        )


class MistralCredentialsDeleteView(LoginRequiredMixin, DeleteView):
    """Delete Mistral credentials."""

    model = MistralCredentials
    template_name = "camille/credential_confirm_delete.html"
    success_url = reverse_lazy("camille:credentials_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["credential_type"] = "Mistral"
        return context

    def get_queryset(self):
        """Only allow deleting credentials owned by the current user."""
        return MistralCredentials.objects.filter(
            user_credential__user_profile=self.request.user.profile
        )
