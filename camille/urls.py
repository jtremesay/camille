from django.urls import path

from . import views

app_name = "camille"

urlpatterns = [
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
]
