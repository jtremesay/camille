from datetime import UTC, datetime, timedelta

from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from django.test import TestCase
from pydantic_ai.messages import ModelRequest, UserPromptPart
from pydantic_ai_harness.step_persistence import (
    ContinuableSnapshot,
    RunRecord,
    StepEvent,
    ToolEffectRecord,
)

from pydantic_ai_django.models import (
    DjangoContinuableSnapshot,
    DjangoRunRecord,
    DjangoStepEvent,
    DjangoToolEffectRecord,
)
from pydantic_ai_django.models.step_persistence.continuable_snapshot import (
    snapshot_state_len,
    validate_is_snapshot_state,
)
from pydantic_ai_django.models.step_persistence.step_event import (
    event_kind_len,
    validate_is_event_kind,
)
from pydantic_ai_django.models.step_persistence.tool_effect_record import (
    tool_effect_status_len,
    validate_is_tool_effect_status,
)
from pydantic_ai_django.step_persistence import DjangoMemoryStore
from pydantic_ai_django.validators import validate_is_dict

STARTED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def make_run_record(run_id: str = "run-1", **kwargs) -> RunRecord:
    return RunRecord(
        run_id=run_id,
        conversation_id=kwargs.pop("conversation_id", "conv-1"),
        agent_name=kwargs.pop("agent_name", "Camille"),
        metadata=kwargs.pop("metadata", {"source": "test"}),
        started_at=kwargs.pop("started_at", STARTED_AT),
        **kwargs,
    )


class DjangoStepPersistenceStoreTests(TestCase):
    def setUp(self):
        self.store = DjangoMemoryStore()

    def register(self, run_id: str = "run-1", **kwargs) -> RunRecord:
        record = make_run_record(run_id, **kwargs)
        async_to_sync(self.store.register_run)(record)

        return record

    def test_register_and_get_run_round_trip(self):
        record = self.register()

        self.assertEqual(async_to_sync(self.store.get_run)(run_id="run-1"), record)

    def test_get_run_returns_none_for_an_unknown_run(self):
        self.assertIsNone(async_to_sync(self.store.get_run)(run_id="missing"))

    def test_list_runs_is_ordered_by_start_time(self):
        self.register("run-2", started_at=STARTED_AT + timedelta(minutes=1))
        self.register("run-1")

        runs = async_to_sync(self.store.list_runs)()

        self.assertEqual([run.run_id for run in runs], ["run-1", "run-2"])

    def test_list_runs_filters_by_parent_run(self):
        self.register("run-1")
        self.register("run-2", parent_run_id="run-1")

        runs = async_to_sync(self.store.list_runs)(parent_run_id="run-1")

        self.assertEqual([run.run_id for run in runs], ["run-2"])
        self.assertEqual(runs[0].parent_run_id, "run-1")

    def test_list_runs_filters_by_conversation(self):
        self.register("run-1", conversation_id="conv-1")
        self.register("run-2", conversation_id="conv-2")

        runs = async_to_sync(self.store.list_runs)(conversation_id="conv-2")

        self.assertEqual([run.run_id for run in runs], ["run-2"])

    def test_append_and_list_events(self):
        self.register()
        event = StepEvent(
            run_id="run-1",
            kind="run_started",
            step_index=0,
            timestamp=STARTED_AT,
            conversation_id="conv-1",
            agent_name="Camille",
            metadata={"source": "test"},
        )

        async_to_sync(self.store.append_event)(event)

        self.assertEqual(async_to_sync(self.store.list_events)(run_id="run-1"), [event])

    def test_list_events_is_scoped_to_the_run(self):
        self.register("run-1")
        self.register("run-2")
        async_to_sync(self.store.append_event)(
            StepEvent(run_id="run-2", kind="run_started", step_index=0)
        )

        self.assertEqual(async_to_sync(self.store.list_events)(run_id="run-1"), [])

    def test_save_and_read_latest_snapshot(self):
        self.register()
        messages = [ModelRequest(parts=[UserPromptPart(content="hello")])]
        async_to_sync(self.store.save_snapshot)(
            ContinuableSnapshot(
                run_id="run-1", step_index=0, messages=messages, timestamp=STARTED_AT
            )
        )
        async_to_sync(self.store.save_snapshot)(
            ContinuableSnapshot(
                run_id="run-1", step_index=1, messages=messages, timestamp=STARTED_AT
            )
        )

        snapshot = async_to_sync(self.store.latest_snapshot)(run_id="run-1")

        self.assertEqual(snapshot.step_index, 1)
        self.assertEqual(snapshot.messages, messages)
        self.assertEqual(snapshot.state, "complete")

    def test_latest_snapshot_skips_interrupted_snapshots_by_default(self):
        self.register()
        async_to_sync(self.store.save_snapshot)(
            ContinuableSnapshot(
                run_id="run-1", step_index=0, messages=[], state="complete"
            )
        )
        async_to_sync(self.store.save_snapshot)(
            ContinuableSnapshot(
                run_id="run-1", step_index=1, messages=[], state="interrupted"
            )
        )

        self.assertEqual(
            async_to_sync(self.store.latest_snapshot)(run_id="run-1").step_index, 0
        )
        self.assertEqual(
            async_to_sync(self.store.latest_snapshot)(
                run_id="run-1", include_interrupted=True
            ).step_index,
            1,
        )

    def test_latest_snapshot_returns_none_when_there_is_none(self):
        self.register()

        self.assertIsNone(async_to_sync(self.store.latest_snapshot)(run_id="run-1"))

    def test_record_and_get_tool_effect(self):
        self.register()
        record = ToolEffectRecord(
            tool_call_id="call-1",
            tool_name="search",
            run_id="run-1",
            status="started",
            started_at=STARTED_AT,
        )

        async_to_sync(self.store.record_tool_effect)(record)

        self.assertEqual(
            async_to_sync(self.store.get_tool_effect)(
                run_id="run-1", tool_call_id="call-1"
            ),
            record,
        )

    def test_record_tool_effect_updates_an_existing_record(self):
        self.register()
        started = ToolEffectRecord(
            tool_call_id="call-1",
            tool_name="search",
            run_id="run-1",
            status="started",
            started_at=STARTED_AT,
        )
        async_to_sync(self.store.record_tool_effect)(started)

        async_to_sync(self.store.record_tool_effect)(
            ToolEffectRecord(
                tool_call_id="call-1",
                tool_name="search",
                run_id="run-1",
                status="completed",
                started_at=STARTED_AT,
                ended_at=STARTED_AT + timedelta(seconds=2),
                effect_summary="done",
            )
        )

        self.assertEqual(DjangoToolEffectRecord.objects.count(), 1)
        effect = async_to_sync(self.store.get_tool_effect)(
            run_id="run-1", tool_call_id="call-1"
        )
        self.assertEqual(effect.status, "completed")
        self.assertEqual(effect.effect_summary, "done")

    def test_get_tool_effect_returns_none_for_an_unknown_call(self):
        self.register()

        self.assertIsNone(
            async_to_sync(self.store.get_tool_effect)(
                run_id="run-1", tool_call_id="missing"
            )
        )

    def test_list_unresolved_tool_effects_only_returns_started_ones(self):
        self.register()
        for tool_call_id, status in (("call-1", "started"), ("call-2", "completed")):
            async_to_sync(self.store.record_tool_effect)(
                ToolEffectRecord(
                    tool_call_id=tool_call_id,
                    tool_name="search",
                    run_id="run-1",
                    status=status,
                    started_at=STARTED_AT,
                )
            )

        unresolved = async_to_sync(self.store.list_unresolved_tool_effects)(
            run_id="run-1"
        )

        self.assertEqual([effect.tool_call_id for effect in unresolved], ["call-1"])


class StepPersistenceValidatorTests(TestCase):
    def test_validate_is_dict(self):
        self.assertIsNone(validate_is_dict({"a": "b"}))

        with self.assertRaises(ValidationError):
            validate_is_dict(["a"])

    def test_validate_is_event_kind(self):
        self.assertIsNone(validate_is_event_kind("run_started"))

        with self.assertRaises(ValueError):
            validate_is_event_kind("napping")

    def test_validate_is_snapshot_state(self):
        self.assertIsNone(validate_is_snapshot_state("complete"))

        with self.assertRaises(ValueError):
            validate_is_snapshot_state("napping")

    def test_validate_is_tool_effect_status(self):
        self.assertIsNone(validate_is_tool_effect_status("started"))

        with self.assertRaises(ValueError):
            validate_is_tool_effect_status("napping")

    def test_field_lengths_fit_the_longest_allowed_value(self):
        self.assertGreaterEqual(event_kind_len(), len("run_started"))
        self.assertGreaterEqual(snapshot_state_len(), len("complete"))
        self.assertGreaterEqual(tool_effect_status_len(), len("started"))


class StepPersistenceModelTests(TestCase):
    def test_run_record_without_a_parent_round_trips(self):
        DjangoRunRecord.objects.create(
            id="run-1", agent_name="Camille", started_at=STARTED_AT
        )

        record = DjangoRunRecord.objects.get(id="run-1").to_pydanticai()

        self.assertIsNone(record.parent_run_id)
        self.assertEqual(record.agent_name, "Camille")

    def test_step_event_metadata_must_be_a_dict(self):
        DjangoRunRecord.objects.create(id="run-1", started_at=STARTED_AT)
        event = DjangoStepEvent(
            run_id="run-1",
            kind="run_started",
            step_index=0,
            timestamp=STARTED_AT,
            metadata=["nope"],
        )

        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_continuable_snapshot_messages_round_trip(self):
        DjangoRunRecord.objects.create(id="run-1", started_at=STARTED_AT)
        messages = [ModelRequest(parts=[UserPromptPart(content="hello")])]
        async_to_sync(DjangoContinuableSnapshot.objects.acreate_from_pydanticai)(
            ContinuableSnapshot(run_id="run-1", step_index=0, messages=messages)
        )

        snapshot = DjangoContinuableSnapshot.objects.get().to_pydanticai()

        self.assertEqual(snapshot.messages, messages)
