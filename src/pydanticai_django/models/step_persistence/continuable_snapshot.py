from typing import get_args

from django.db import models
from pydantic_ai.messages import ModelMessagesTypeAdapter
from pydantic_ai_harness.step_persistence import ContinuableSnapshot, SnapshotState


def validate_is_snapshot_state(value):
    if value not in get_args(SnapshotState):
        raise ValueError(f"Value '{value}' is not a valid SnapshotState.")


class DjangoContinuableSnapshotManager(models.Manager):
    async def acreate_from_pydanticai(
        self, snapshot: ContinuableSnapshot
    ) -> DjangoContinuableSnapshot:
        return await self.acreate(
            run_id=snapshot.run_id,
            step_index=snapshot.step_index,
            messages=ModelMessagesTypeAdapter.dump_json(snapshot.messages),
            conversation_id=snapshot.conversation_id,
            parent_run_id=snapshot.parent_run_id,
            agent_name=snapshot.agent_name,
            timestamp=snapshot.timestamp,
            state=snapshot.state,
            idempotency_key=snapshot.idempotency_key,
        )


class DjangoContinuableSnapshot(models.Model):
    objects = DjangoContinuableSnapshotManager()

    run = models.ForeignKey(
        "pydanticai_django.DjangoRunRecord",
        on_delete=models.CASCADE,
        related_name="continuable_snapshots",
        related_query_name="continuable_snapshot",
    )
    step_index = models.IntegerField()
    messages = models.BinaryField()
    conversation_id = models.CharField(max_length=255, null=True, blank=True)
    parent_run = models.ForeignKey(
        "pydanticai_django.DjangoRunRecord",
        on_delete=models.CASCADE,
        related_name="child_continuable_snapshots",
        related_query_name="child_continuable_snapshot",
        null=True,
        blank=True,
    )
    agent_name = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField()
    state = models.CharField(max_length=255, validators=[validate_is_snapshot_state])
    idempotency_key = models.CharField(max_length=255, null=True, blank=True)

    def to_pydanticai(self) -> ContinuableSnapshot:
        return ContinuableSnapshot(
            run_id=self.run_id,
            step_index=self.step_index,
            messages=ModelMessagesTypeAdapter.validate_json(self.messages),
            conversation_id=self.conversation_id,
            parent_run_id=self.parent_run_id,
            agent_name=self.agent_name,
            timestamp=self.timestamp,
            state=self.state,
            idempotency_key=self.idempotency_key,
        )
