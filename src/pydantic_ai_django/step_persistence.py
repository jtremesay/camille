from pydantic_ai_harness.step_persistence import (
    ContinuableSnapshot,
    RunRecord,
    StepEvent,
    ToolEffectRecord,
)

from .models import (
    DjangoContinuableSnapshot,
    DjangoRunRecord,
    DjangoStepEvent,
    DjangoToolEffectRecord,
)


class DjangoMemoryStore:
    async def register_run(self, record: RunRecord) -> None:
        await DjangoRunRecord.objects.acreate_from_pydanticai(record)

    async def get_run(self, *, run_id: str) -> RunRecord | None:
        try:
            record = await DjangoRunRecord.objects.aget(id=run_id)
        except DjangoRunRecord.DoesNotExist:
            return None

        return record.to_pydanticai()

    async def list_runs(
        self,
        *,
        parent_run_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[RunRecord]:
        qs = DjangoRunRecord.objects.order_by("started_at")
        if parent_run_id is not None:
            qs = qs.filter(parent_run_id=parent_run_id)
        if conversation_id is not None:
            qs = qs.filter(conversation_id=conversation_id)

        return [o.to_pydanticai() async for o in qs]

    async def append_event(self, event: StepEvent) -> None:
        await DjangoStepEvent.objects.acreate_from_pydanticai(event)

    async def list_events(self, *, run_id: str) -> list[StepEvent]:
        qs = DjangoStepEvent.objects.filter(run_id=run_id).order_by("id")

        return [o.to_pydanticai() async for o in qs]

    async def save_snapshot(self, snapshot: ContinuableSnapshot) -> None:
        await DjangoContinuableSnapshot.objects.acreate_from_pydanticai(snapshot)

    async def latest_snapshot(
        self, *, run_id: str, include_interrupted: bool = False
    ) -> ContinuableSnapshot | None:
        qs = DjangoContinuableSnapshot.objects.filter(run_id=run_id).order_by("-id")
        if not include_interrupted:
            qs = qs.filter(state="complete")

        if (snapshot := await qs.afirst()) is not None:
            return snapshot.to_pydanticai()

        return None

    async def record_tool_effect(self, record: ToolEffectRecord) -> None:
        await DjangoToolEffectRecord.objects.aupdate_or_create_from_pydanticai(record)

    async def get_tool_effect(
        self, *, run_id: str, tool_call_id: str
    ) -> ToolEffectRecord | None:
        try:
            effect = await DjangoToolEffectRecord.objects.aget(
                run_id=run_id, tool_call_id=tool_call_id
            )
        except DjangoToolEffectRecord.DoesNotExist:
            return None

        return effect.to_pydanticai()

    async def list_unresolved_tool_effects(
        self, *, run_id: str
    ) -> list[ToolEffectRecord]:
        qs = DjangoToolEffectRecord.objects.filter(run_id=run_id, status="started")

        return [o.to_pydanticai() async for o in qs]
