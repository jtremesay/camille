from django.urls import path

from . import views

app_name = "camille"

urlpatterns = [
    # Landing page for unauthenticated users
    path("", views.LandingPageView.as_view(), name="landing"),
    # Home page for authenticated users
    path("home/", views.HomeView.as_view(), name="home"),
    # Logout confirmation
    path("logout/", views.LogoutConfirmView.as_view(), name="logout_confirm"),
    # Dashboard - list all credentials
    path("credentials/", views.CredentialsListView.as_view(), name="credentials_list"),
    # AWS Bedrock Credentials
    path(
        "credentials/aws/add/",
        views.AwsBedrockCredentialsCreateView.as_view(),
        name="aws_credentials_create",
    ),
    path(
        "credentials/aws/<int:pk>/edit/",
        views.AwsBedrockCredentialsUpdateView.as_view(),
        name="aws_credentials_update",
    ),
    path(
        "credentials/aws/<int:pk>/delete/",
        views.AwsBedrockCredentialsDeleteView.as_view(),
        name="aws_credentials_delete",
    ),
    # Google GLA Credentials
    path(
        "credentials/google/add/",
        views.GoogleGlaCredentialsCreateView.as_view(),
        name="google_credentials_create",
    ),
    path(
        "credentials/google/<int:pk>/edit/",
        views.GoogleGlaCredentialsUpdateView.as_view(),
        name="google_credentials_update",
    ),
    path(
        "credentials/google/<int:pk>/delete/",
        views.GoogleGlaCredentialsDeleteView.as_view(),
        name="google_credentials_delete",
    ),
    # Mistral Credentials
    path(
        "credentials/mistral/add/",
        views.MistralCredentialsCreateView.as_view(),
        name="mistral_credentials_create",
    ),
    path(
        "credentials/mistral/<int:pk>/edit/",
        views.MistralCredentialsUpdateView.as_view(),
        name="mistral_credentials_update",
    ),
    path(
        "credentials/mistral/<int:pk>/delete/",
        views.MistralCredentialsDeleteView.as_view(),
        name="mistral_credentials_delete",
    ),
    # Mattermost Servers
    path(
        "mattermost/",
        views.MattermostServerListView.as_view(),
        name="mattermost_list",
    ),
    path(
        "mattermost/add/",
        views.MattermostServerCreateView.as_view(),
        name="mattermost_create",
    ),
    path(
        "mattermost/<int:pk>/edit/",
        views.MattermostServerUpdateView.as_view(),
        name="mattermost_update",
    ),
    path(
        "mattermost/<int:pk>/delete/",
        views.MattermostServerDeleteView.as_view(),
        name="mattermost_delete",
    ),
]
