from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """An extension to the default User model to store additional user information."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )

    def __str__(self):
        return self.user.username


# Auto-create a profile when a new user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class BaseCredentials(models.Model):
    """Base model for different types of credentials."""

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ApiKeyCredentials(BaseCredentials):
    """For providers using simple API key authentication (Google, Mistral, etc.)"""

    api_key = models.CharField(max_length=255)


class AwsBedrockCredentials(ApiKeyCredentials):
    """Credentials for AWS Bedrock API"""

    region_name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "AWS Bedrock Credentials"
        verbose_name_plural = "AWS Bedrock Credentials"


class GoogleGlaCredentials(ApiKeyCredentials):
    """Credentials for Google Generative Language API"""

    class Meta:
        verbose_name = "Google GLA Credentials"
        verbose_name_plural = "Google GLA Credentials"


class MistralCredentials(ApiKeyCredentials):
    """Credentials for Mistral API"""

    class Meta:
        verbose_name = "Mistral Credentials"
        verbose_name_plural = "Mistral Credentials"


class UserCredentials(models.Model):
    """Link user profiles to their credentials for various providers."""

    user_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="credentials",
        related_query_name="credential",
    )
    credentials = models.OneToOneField(
        BaseCredentials,
        on_delete=models.CASCADE,
        related_name="user_credentials",
        related_query_name="user_credential",
    )

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.credentials.name}"


class MattermostServer(models.Model):
    """A Mattermost server"""

    name = models.CharField(max_length=255)
    base_url = models.URLField()
    api_token = models.CharField(max_length=255)

    def __str__(self):
        return self.name
