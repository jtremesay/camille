from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class MattermostBinding(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="mm_binding"
    )
    mm_id = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.user.username


class AgentPersonality(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="personalities"
    )
    name = models.SlugField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    prompt_template = models.TextField()

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return self.name


class AgentConfig(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="agent_config"
    )
    model = models.CharField(
        max_length=64, help_text="https://pydantic.dev/docs/ai/models/overview/"
    )
    personality = models.ForeignKey(
        AgentPersonality, on_delete=models.SET_NULL, null=True, blank=True
    )
    instructions = models.TextField(
        blank=True
    )  # Additional instructions to the agent, appended to the personality prompt
    notes = models.TextField(blank=True)  # Managed by the agent

    def clean(self):
        if self.personality and self.personality.user != self.user:
            raise ValueError("Personality must belong to the same user.")

        super().clean()


# Create agent config on user creation
@receiver(post_save, sender=User)
def create_agent_config(sender, instance, created, **kwargs):
    if created:
        AgentConfig.objects.create(
            user=instance,
            personality=AgentPersonality.objects.create(
                user=instance,
                name="camille",
                description="The default personality.",
                prompt_template=settings.DEFAULT_PROMPT_TEMPLATE,
            ),
        )
