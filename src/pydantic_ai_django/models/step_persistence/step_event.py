from typing import get_args

from django.db import models
from pydantic_ai_harness.step_persistence import EventKind, StepEvent

from pydantic_ai_django.validators import validate_is_dict


def event_kind_len() -> int:
    return max(len(kind) for kind in get_args(EventKind))


def validate_is_event_kind(value):
    if value not in get_args(EventKind):
        raise ValueError(f"Value '{value}' is not a valid EventKind.")


class DjangoStepEventManager(models.Manager):
    async def acreate_from_pydanticai(self, event: StepEvent) -> DjangoStepEvent:
        return await self.acreate(
            run_id=event.run_id,
            kind=event.kind,
            step_index=event.step_index,
            timestamp=event.timestamp,
            conversation_id=event.conversation_id,
            parent_run_id=event.parent_run_id,
            agent_name=event.agent_name,
            tool_call_id=event.tool_call_id,
            tool_name=event.tool_name,
            error=event.error,
            metadata=event.metadata,
            idempotency_key=event.idempotency_key,
        )


class DjangoStepEvent(models.Model):
    objects = DjangoStepEventManager()

    run = models.ForeignKey(
        "pydantic_ai_django.DjangoRunRecord",
        on_delete=models.CASCADE,
        related_name="step_events",
        related_query_name="step_event",
    )
    kind = models.CharField(
        max_length=event_kind_len(),
        validators=[validate_is_event_kind],
    )
    step_index = models.IntegerField()
    timestamp = models.DateTimeField()
    conversation_id = models.CharField(max_length=255, null=True, blank=True)
    parent_run = models.ForeignKey(
        "pydantic_ai_django.DjangoRunRecord",
        on_delete=models.CASCADE,
        related_name="child_step_events",
        related_query_name="child_step_event",
        null=True,
        blank=True,
    )
    agent_name = models.CharField(max_length=255, null=True, blank=True)
    tool_call_id = models.CharField(max_length=255, null=True, blank=True)
    tool_name = models.CharField(max_length=255, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True, validators=[validate_is_dict])
    idempotency_key = models.CharField(max_length=255, null=True, blank=True)

    def to_pydanticai(self) -> StepEvent:
        return StepEvent(
            run_id=self.run_id,
            kind=self.kind,
            step_index=self.step_index,
            timestamp=self.timestamp,
            conversation_id=self.conversation_id,
            parent_run_id=self.parent_run_id,
            agent_name=self.agent_name,
            tool_call_id=self.tool_call_id,
            tool_name=self.tool_name,
            error=self.error,
            metadata=self.metadata,
            idempotency_key=self.idempotency_key,
        )
