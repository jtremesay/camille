from itertools import chain

from django.db import models
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter


class MMTeam(models.Model):
    id = models.CharField(primary_key=True, max_length=26)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name or "Unnamed Team"


class MMChannel(models.Model):
    class Type(models.TextChoices):
        OPEN = "O", "Open"
        PRIVATE = "P", "Private"
        DIRECT = "D", "Direct"
        GROUP = "G", "Group"

    id = models.CharField(primary_key=True, max_length=26)
    team = models.ForeignKey(
        MMTeam,
        on_delete=models.CASCADE,
        related_name="channels",
        related_query_name="channel",
    )
    type = models.CharField(max_length=1, choices=Type.choices)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    header = models.TextField(null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)

    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name or "Unnamed Channel"


class MMUser(models.Model):
    id = models.CharField(primary_key=True, max_length=26)
    username = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)

    notes = models.TextField(blank=True)

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


class MMThread(models.Model):
    id = models.CharField(primary_key=True, max_length=26)
    channel = models.ForeignKey(
        MMChannel,
        on_delete=models.CASCADE,
        related_name="threads",
        related_query_name="thread",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    async def get_history(self) -> list[ModelMessage]:
        history = []
        async for m in self.interactions.order_by("created_at").values_list(
            "messages_json", flat=True
        ):
            history.extend(ModelMessagesTypeAdapter.validate_json(m))

        return history

    async def append_interaction(self, post_id: str, result: AgentRunResult) -> None:
        await self.interactions.acreate(
            id=post_id,
            messages_json=result.new_messages_json().decode(),
        )


class MMInteraction(models.Model):
    id = models.CharField(primary_key=True, max_length=26)
    thread = models.ForeignKey(
        MMThread,
        on_delete=models.CASCADE,
        related_name="interactions",
        related_query_name="interaction",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    messages_json = models.TextField()
