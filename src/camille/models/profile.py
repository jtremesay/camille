from typing import TYPE_CHECKING, cast
from uuid import uuid7

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from .agent import Agent
    from .ai import AIModel


class Profile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )

    default_agent = models.ForeignKey(
        "camille.Agent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_profiles",
        related_query_name="default_for_profile",
    )

    default_model = models.ForeignKey(
        "camille.AIModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_profiles",
        related_query_name="default_for_profile",
    )

    def clean(self):
        super().clean()

        if (
            self.default_agent is not None
            and cast("Agent", self.default_agent).user != self.user
        ):
            raise ValidationError("The default agent must belong to the same user.")

        if (
            self.default_model is not None
            and cast("AIModel", self.default_model).user != self.user
        ):
            raise ValidationError("The default model must belong to the same user.")

    def __str__(self) -> str:
        return cast(str, cast("User", self.user).username)


@receiver(post_save, sender="auth.User")
def create_user_profile(
    sender: type[User], instance: User, created: bool, **kwargs
) -> None:
    """Create a Profile instance whenever a new User is created."""
    if not created:
        return

    Profile.objects.create(user=instance)
