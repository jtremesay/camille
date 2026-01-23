from uuid import uuid7

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


class Organization(models.Model):
    uuid = models.UUIDField(default=uuid7, unique=True, editable=False)
    slug = models.SlugField(unique=True, blank=True)
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Team(models.Model):
    uuid = models.UUIDField(default=uuid7, unique=True, editable=False)
    slug = models.SlugField(unique=True, blank=True)
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TeamToOrganization(models.Model):
    uuid = models.UUIDField(default=uuid7, unique=True, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="team_relationships",
        related_query_name="team_relationship",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="organization_relationships",
        related_query_name="organization_relationship",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("organization", "team")

    def __str__(self):
        return f"{self.team} in {self.organization}"


class Profile(models.Model):
    uuid = models.UUIDField(default=uuid7, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.user.username


# create profile when user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class UserToOrganization(models.Model):
    uuid = models.UUIDField(default=uuid7, unique=True, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="user_relationships",
        related_query_name="user_relationship",
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="organization_relationships",
        related_query_name="organization_relationship",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("organization", "profile")

    def __str__(self):
        return f"{self.profile} in {self.organization}"


class UserToTeam(models.Model):
    uuid = models.UUIDField(default=uuid7, unique=True, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="user_relationships",
        related_query_name="user_relationship",
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="team_relationships",
        related_query_name="team_relationship",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("team", "profile")

    def __str__(self):
        return f"{self.profile} in {self.team}"
