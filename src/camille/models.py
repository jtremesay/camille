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


class MattermostTeam(models.Model):
    server = models.ForeignKey(
        MattermostServer,
        on_delete=models.CASCADE,
        related_name="teams",
        related_query_name="team",
    )
    team_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()

    class Meta:
        unique_together = ("server", "team_id")

    def __str__(self) -> str:
        return self.name


class MattermostUser(models.Model):
    server = models.ForeignKey(
        MattermostServer,
        on_delete=models.CASCADE,
        related_name="users",
        related_query_name="user",
    )
    user_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()

    class Meta:
        unique_together = ("server", "user_id")

    def __str__(self) -> str:
        return self.username


class MattermostChannel(models.Model):
    team = models.ForeignKey(
        MattermostTeam,
        on_delete=models.CASCADE,
        related_name="channels",
        related_query_name="channel",
    )
    channel_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    header = models.TextField()
    purpose = models.TextField()
    last_post_at = models.DateTimeField()
    create_at = models.DateTimeField()
    update_at = models.DateTimeField()

    class Meta:
        unique_together = ("team", "channel_id")

    def __str__(self) -> str:
        return self.name


class MattermostChannelMember(models.Model):
    channel = models.ForeignKey(
        MattermostChannel,
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
    )
    user = models.ForeignKey(
        MattermostUser,
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
    )

    class Meta:
        unique_together = ("channel", "user")

    def __str__(self) -> str:
        return f"{self.user.username} in {self.channel.name}"

    def save(self, *args, **kwargs) -> None:
        if self.channel.team.server != self.user.server:
            raise ValueError(
                "Channel and User must belong to the same Mattermost server."
            )

        super().save(*args, **kwargs)


class ProfileMattermostMapping(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="mm_mappings",
        related_query_name="mm_mapping",
    )
    mm_user = models.OneToOneField(
        MattermostUser,
        on_delete=models.CASCADE,
        related_name="mm_mappings",
        related_query_name="mm_mapping",
    )

    class Meta:
        unique_together = ("profile", "mm_user")

    def __str__(self) -> str:
        return f"{self.profile.user.username} -> {self.mm_user.username}"
