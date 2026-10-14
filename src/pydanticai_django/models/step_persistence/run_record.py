from django.db import models
from pydantic_ai_harness.step_persistence import (
    RunRecord,
)

from pydanticai_django.validators import validate_is_dict


class DjangoRunRecordManager(models.Manager):
    async def acreate_from_pydanticai(self, run_record: RunRecord) -> DjangoRunRecord:
        return await self.acreate(
            id=run_record.run_id,
            conversation_id=run_record.conversation_id,
            parent_run_id=run_record.parent_run_id,
            agent_name=run_record.agent_name,
            metadata=run_record.metadata,
            started_at=run_record.started_at,
            registration_id=run_record.registration_id,
        )


class DjangoRunRecord(models.Model):
    objects = DjangoRunRecordManager()

    id = models.CharField(max_length=255, primary_key=True)
    conversation_id = models.CharField(max_length=255, null=True, blank=True)
    parent_run = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_runs",
        related_query_name="child_run",
    )
    agent_name = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, validators=[validate_is_dict])
    started_at = models.DateTimeField()
    registration_id = models.CharField(max_length=255, null=True, blank=True)

    def to_pydanticai(self) -> RunRecord:
        return RunRecord(
            run_id=self.id,
            conversation_id=self.conversation_id,
            parent_run_id=self.parent_run_id if self.parent_run else None,
            agent_name=self.agent_name,
            metadata=self.metadata,
            started_at=self.started_at,
            registration_id=self.registration_id,
        )
