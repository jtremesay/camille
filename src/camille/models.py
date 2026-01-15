from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class InferenceProvider(models.TextChoices):
    AWS_BEDROCK = "aws_bedrock", "AWS Bedrock"
    GOOGLE_GLA = "google_gla", "Google Generative AI"
    MISTRAL_AI = "mistral_ai", "Mistral AI"


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_on_user_create(
    sender: type[AbstractBaseUser], instance: AbstractBaseUser, created: bool, **kwargs
) -> None:
    if created:
        Profile.objects.create(user=instance)


class UserInferenceProviderCredentials(models.Model):
    class Meta:
        unique_together = ("profile", "provider")
        abstract = True

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    provider = models.CharField(
        max_length=50,
        choices=InferenceProvider.choices,
    )


class UserAWSBedrockInferenceProviderCredentials(UserInferenceProviderCredentials):
    api_key = models.TextField()
    region_name = models.CharField(max_length=100)

    def save(self, *args, **kwargs) -> None:
        self.provider = InferenceProvider.AWS_BEDROCK
        super().save(*args, **kwargs)


class UserGoogleGLAInferenceProviderCredentials(UserInferenceProviderCredentials):
    api_key = models.TextField()

    def save(self, *args, **kwargs) -> None:
        self.provider = InferenceProvider.GOOGLE_GLA
        super().save(*args, **kwargs)


class UserMistralAIInferenceProviderCredentials(UserInferenceProviderCredentials):
    api_key = models.TextField()

    def save(self, *args, **kwargs) -> None:
        self.provider = InferenceProvider.MISTRAL_AI
        super().save(*args, **kwargs)


class MattermostServer(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    token = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name
