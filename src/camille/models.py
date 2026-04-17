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


class AgentPersonality(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="personalities"
    )
    name = models.SlugField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    prompt_template = models.TextField()

    class Meta:
        unique_together = ("user", "name")


# Create personalities on user creation
@receiver(post_save, sender=User)
def create_personalities(sender, instance, created, **kwargs):
    if created:
        AgentPersonality.objects.create(
            user=instance,
            name="camille",
            description="The default personality.",
            prompt_template=settings.DEFAULT_PROMPT_TEMPLATE,
        )
