from django.db import models


class MMTeam(models.Model):
    id = models.CharField(primary_key=True, max_length=26)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name or "Unnamed Team"


class MMChannel(models.Model):
    class Type(models.TextChoices):
        OPEN = "O"
        PRIVATE = "P"
        DIRECT = "D"
        GROUP = "G"

    id = models.CharField(primary_key=True, max_length=26)
    team = models.ForeignKey(
        MMTeam,
        on_delete=models.CASCADE,
        related_name="channels",
        related_query_name="channel",
    )
    type = models.CharField(max_length=1, choices=Type.choices)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    header = models.TextField(null=True)
    purpose = models.TextField(null=True)

    def __str__(self):
        return self.name or "Unnamed Channel"


class MMUser(models.Model):
    id = models.CharField(primary_key=True, max_length=26)
    username = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.username or "Unnamed User"


class MMMembership(models.Model):
    class Meta:
        unique_together = ("channel", "user")

    channel = models.ForeignKey(
        MMChannel,
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
    )
    user = models.ForeignKey(
        MMUser,
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
    )
