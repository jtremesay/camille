"""
URL configuration for proj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from camille import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Agent management
    path(
        "agent/config/edit/",
        views.AgentConfigEditView.as_view(),
        name="agent_config_update",
    ),
    path(
        "agent/personalities/create/",
        views.AgentPersonalityCreateView.as_view(),
        name="agent_personality_create",
    ),
    path(
        "agent/personalities/<int:pk>/edit/",
        views.AgentPersonalityUpdateView.as_view(),
        name="agent_personality_update",
    ),
    path(
        "agent/personalities/<int:pk>/delete/",
        views.AgentPersonalityDeleteView.as_view(),
        name="agent_personality_delete",
    ),
    # Credentials management
    path(
        "credentials/anthropic/create/",
        views.AnthropicCredentialsCreateView.as_view(),
        name="anthropic_credentials_create",
    ),
    path(
        "credentials/anthropic/edit/",
        views.AnthropicCredentialsUpdateView.as_view(),
        name="anthropic_credentials_update",
    ),
    path(
        "credentials/anthropic/delete/",
        views.AnthropicCredentialsDeleteView.as_view(),
        name="anthropic_credentials_delete",
    ),
    path(
        "credentials/awsbedrock/create/",
        views.AWSBedrockCredentialsCreateView.as_view(),
        name="awsbedrock_credentials_create",
    ),
    path(
        "credentials/awsbedrock/edit/",
        views.AWSBedrockCredentialsUpdateView.as_view(),
        name="awsbedrock_credentials_update",
    ),
    path(
        "credentials/awsbedrock/delete/",
        views.AWSBedrockCredentialsDeleteView.as_view(),
        name="awsbedrock_credentials_delete",
    ),
    path(
        "credentials/gateway/create/",
        views.GatewayCredentialsCreateView.as_view(),
        name="gateway_credentials_create",
    ),
    path(
        "credentials/gateway/edit/",
        views.GatewayCredentialsUpdateView.as_view(),
        name="gateway_credentials_update",
    ),
    path(
        "credentials/gateway/delete/",
        views.GatewayCredentialsDeleteView.as_view(),
        name="gateway_credentials_delete",
    ),
    path(
        "credentials/googlegla/create/",
        views.GoogleGLACredentialsCreateView.as_view(),
        name="googlegla_credentials_create",
    ),
    path(
        "credentials/googlegla/edit/",
        views.GoogleGLACredentialsUpdateView.as_view(),
        name="googlegla_credentials_update",
    ),
    path(
        "credentials/googlegla/delete/",
        views.GoogleGLACredentialsDeleteView.as_view(),
        name="googlegla_credentials_delete",
    ),
    path(
        "credentials/mistral/create/",
        views.MistralCredentialsCreateView.as_view(),
        name="mistral_credentials_create",
    ),
    path(
        "credentials/mistral/edit/",
        views.MistralCredentialsUpdateView.as_view(),
        name="mistral_credentials_update",
    ),
    path(
        "credentials/mistral/delete/",
        views.MistralCredentialsDeleteView.as_view(),
        name="mistral_credentials_delete",
    ),
    path(
        "credentials/openrouter/create/",
        views.OpenRouterCredentialsCreateView.as_view(),
        name="openrouter_credentials_create",
    ),
    path(
        "credentials/openrouter/edit/",
        views.OpenRouterCredentialsUpdateView.as_view(),
        name="openrouter_credentials_update",
    ),
    path(
        "credentials/openrouter/delete/",
        views.OpenRouterCredentialsDeleteView.as_view(),
        name="openrouter_credentials_delete",
    ),
    # Mattermost integration
    path(
        "mattermost/bind/",
        views.MattermostBindCreateView.as_view(),
        name="mattermost_bind",
    ),
    path(
        "mattermost/unbind/",
        views.MattermostBindDeleteView.as_view(),
        name="mattermost_unbind",
    ),
    # Account management
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path(
        "accounts/logout_confirm/",
        views.LogoutConfirmView.as_view(),
        name="logout_confirm",
    ),
    path(
        "accounts/update/",
        views.ProfileUpdateView.as_view(),
        name="profile_update",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    # Admin site
    path("admin/", admin.site.urls),
]
