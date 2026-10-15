from typing import get_args

from django.db import models
from pydantic_ai_harness.step_persistence import ToolEffectRecord, ToolEffectStatus


def tool_effect_status_len() -> int:
    return max(len(status) for status in get_args(ToolEffectStatus))


def validate_is_tool_effect_status(value):
    if value not in get_args(ToolEffectStatus):
        raise ValueError(f"Value '{value}' is not a valid ToolEffectStatus.")


class DjangoToolEffectRecordManager(models.Manager):
    async def aupdate_or_create_from_pydanticai(
        self, record: ToolEffectRecord
    ) -> DjangoToolEffectRecord:
        return await self.aupdate_or_create(
            tool_call_id=record.tool_call_id,
            run_id=record.run_id,
            defaults={
                "tool_name": record.tool_name,
                "status": record.status,
                "started_at": record.started_at,
                "ended_at": record.ended_at,
                "idempotency_key": record.idempotency_key,
                "effect_summary": record.effect_summary,
            },
        )


class DjangoToolEffectRecord(models.Model):
    objects = DjangoToolEffectRecordManager()

    tool_call_id = models.CharField(max_length=255)
    tool_name = models.CharField(max_length=255)
    run = models.ForeignKey(
        "DjangoRunRecord",
        on_delete=models.CASCADE,
        related_name="tool_effect_records",
        related_query_name="tool_effect_records",
    )
    status = models.CharField(
        max_length=tool_effect_status_len(), validators=[validate_is_tool_effect_status]
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=255, null=True, blank=True)
    effect_summary = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("tool_call_id", "run")

    def to_pydanticai(self) -> ToolEffectRecord:
        return ToolEffectRecord(
            tool_call_id=self.tool_call_id,
            tool_name=self.tool_name,
            run_id=self.run_id,
            status=self.status,
            started_at=self.started_at,
            ended_at=self.ended_at,
            idempotency_key=self.idempotency_key,
            effect_summary=self.effect_summary,
        )
