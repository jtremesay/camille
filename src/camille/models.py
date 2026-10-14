from uuid import uuid7

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_extensions.db.models import AutoSlugField


class Profile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )


@receiver(post_save, sender=User)
def create_user_profile(
    sender: type[User], instance: User, created: bool, **kwargs
) -> None:
    """Create a Profile instance whenever a new User is created."""
    if not created:
        return

    Profile.objects.create(user=instance)


class Agent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from="name", max_length=255)
    name = models.CharField(max_length=255, default="default")

    class Meta:
        unique_together = ("user", "slug")
