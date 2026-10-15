from django.contrib import admin

from ..models.step_persistence import (
    DjangoContinuableSnapshot,
    DjangoRunRecord,
    DjangoStepEvent,
    DjangoToolEffectRecord,
)


@admin.register(DjangoRunRecord)
class DjangoRunRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation_id",
        "parent_run",
        "agent_name",
        "started_at",
        "registration_id",
    )


@admin.register(DjangoStepEvent)
class DjangoStepEventAdmin(admin.ModelAdmin):
    list_display = (
        "run",
        "kind",
        "step_index",
        "timestamp",
        "conversation_id",
        "parent_run",
        "agent_name",
        "tool_call_id",
        "tool_name",
        "error",
        "metadata",
        "idempotency_key",
    )


@admin.register(DjangoContinuableSnapshot)
class DjangoContinuableSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "run",
        "step_index",
        "conversation_id",
        "parent_run",
        "agent_name",
        "timestamp",
        "state",
        "idempotency_key",
    )


@admin.register(DjangoToolEffectRecord)
class DjangoToolEffectRecordAdmin(admin.ModelAdmin):
    list_display = (
        "tool_call_id",
        "tool_name",
        "run",
        "status",
        "started_at",
        "ended_at",
        "idempotency_key",
        "effect_summary",
    )
