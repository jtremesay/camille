from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError
from django.test import TestCase
from pydantic_ai_harness.planning import PlanEvent, PlanEventType, PlanItem, TaskStatus

from pydantic_ai_django.models.planning import (
    DjangoPlanItem,
    validate_is_list_of_str,
    validate_is_task_status,
)
from pydantic_ai_django.planning import DjangoPlanStore


class RecordingEmitter:
    """Minimal stand-in for `PlanEventEmitter`, which is deprecated upstream."""

    def __init__(self) -> None:
        self.events: list[PlanEvent] = []

    async def emit(self, event: PlanEvent) -> None:
        self.events.append(event)

    @property
    def event_types(self) -> list[PlanEventType]:
        return [event.event_type for event in self.events]


def make_item(item_id: str = "1", content: str = "Write the docs") -> PlanItem:
    return PlanItem(id=item_id, content=content, active_form="Writing the docs")


class DjangoPlanStoreTests(TestCase):
    def setUp(self):
        self.store = DjangoPlanStore(session_id="session")

    def test_add_and_get_item_round_trip(self):
        item = async_to_sync(self.store.add_item)(make_item())

        stored = async_to_sync(self.store.get_item)("1")

        self.assertEqual(stored, item)
        self.assertEqual(stored.content, "Write the docs")
        self.assertEqual(stored.status, TaskStatus.pending)
        self.assertEqual(stored.active_form, "Writing the docs")
        self.assertIsNone(stored.parent_id)
        self.assertEqual(stored.depends_on, [])

    def test_get_item_returns_none_for_an_unknown_id(self):
        self.assertIsNone(async_to_sync(self.store.get_item)("missing"))

    def test_get_items_is_scoped_to_the_session(self):
        async_to_sync(self.store.add_item)(make_item("1", "Mine"))
        async_to_sync(DjangoPlanStore(session_id="other").add_item)(
            make_item("2", "Theirs")
        )

        items = async_to_sync(self.store.get_items)()

        self.assertEqual([item.content for item in items], ["Mine"])

    def test_get_item_is_scoped_to_the_session(self):
        async_to_sync(DjangoPlanStore(session_id="other").add_item)(make_item("1"))

        self.assertIsNone(async_to_sync(self.store.get_item)("1"))

    def test_set_items_replaces_the_session_plan(self):
        async_to_sync(self.store.add_item)(make_item("1", "Old"))

        async_to_sync(self.store.set_items)(
            [make_item("2", "New"), make_item("3", "Newer")]
        )

        items = async_to_sync(self.store.get_items)()
        self.assertEqual([item.id for item in items], ["2", "3"])

    def test_set_items_does_not_touch_other_sessions(self):
        other = DjangoPlanStore(session_id="other")
        async_to_sync(other.add_item)(make_item("1", "Theirs"))

        async_to_sync(self.store.set_items)([make_item("2", "Mine")])

        self.assertEqual(len(async_to_sync(other.get_items)()), 1)

    def test_update_item_changes_every_field(self):
        async_to_sync(self.store.add_item)(make_item())

        updated = async_to_sync(self.store.update_item)(
            "1",
            content="Ship the docs",
            status=TaskStatus.completed,
            active_form="Shipping the docs",
            parent_id="0",
            depends_on=["2"],
        )

        self.assertEqual(updated.content, "Ship the docs")
        self.assertEqual(updated.status, TaskStatus.completed)
        self.assertEqual(updated.active_form, "Shipping the docs")
        self.assertEqual(updated.parent_id, "0")
        self.assertEqual(updated.depends_on, ["2"])
        self.assertEqual(async_to_sync(self.store.get_item)("1"), updated)

    def test_update_item_keeps_unspecified_fields(self):
        async_to_sync(self.store.add_item)(make_item())

        updated = async_to_sync(self.store.update_item)(
            "1", status=TaskStatus.in_progress
        )

        self.assertEqual(updated.content, "Write the docs")
        self.assertEqual(updated.active_form, "Writing the docs")
        self.assertEqual(updated.status, TaskStatus.in_progress)

    def test_update_item_returns_none_for_an_unknown_id(self):
        self.assertIsNone(async_to_sync(self.store.update_item)("missing", content="x"))

    def test_remove_item(self):
        async_to_sync(self.store.add_item)(make_item())

        self.assertTrue(async_to_sync(self.store.remove_item)("1"))
        self.assertEqual(async_to_sync(self.store.get_items)(), [])

    def test_remove_item_returns_false_for_an_unknown_id(self):
        self.assertFalse(async_to_sync(self.store.remove_item)("missing"))


class DjangoPlanStoreEventTests(TestCase):
    def setUp(self):
        self.emitter = RecordingEmitter()
        self.store = DjangoPlanStore(session_id="session", event_emitter=self.emitter)

    def test_add_item_emits_created(self):
        async_to_sync(self.store.add_item)(make_item())

        self.assertEqual(self.emitter.event_types, [PlanEventType.created])
        self.assertEqual(self.emitter.events[0].item.content, "Write the docs")

    def test_update_item_emits_updated(self):
        async_to_sync(self.store.add_item)(make_item())
        self.emitter.events.clear()

        async_to_sync(self.store.update_item)("1", content="Ship the docs")

        self.assertEqual(self.emitter.event_types, [PlanEventType.updated])

    def test_update_item_emits_status_changes(self):
        async_to_sync(self.store.add_item)(make_item())
        self.emitter.events.clear()

        async_to_sync(self.store.update_item)("1", status=TaskStatus.completed)

        self.assertEqual(
            self.emitter.event_types,
            [
                PlanEventType.updated,
                PlanEventType.status_changed,
                PlanEventType.completed,
            ],
        )

    def test_remove_item_emits_deleted(self):
        async_to_sync(self.store.add_item)(make_item())
        self.emitter.events.clear()

        async_to_sync(self.store.remove_item)("1")

        self.assertEqual(self.emitter.event_types, [PlanEventType.deleted])

    def test_remove_item_emits_nothing_for_an_unknown_id(self):
        async_to_sync(self.store.remove_item)("missing")

        self.assertEqual(self.emitter.events, [])


class DjangoPlanItemValidatorTests(TestCase):
    def test_accepts_a_valid_task_status(self):
        self.assertIsNone(validate_is_task_status(TaskStatus.pending.value))

    def test_rejects_an_invalid_task_status(self):
        with self.assertRaises(ValidationError):
            validate_is_task_status("sleeping")

    def test_accepts_a_list_of_strings(self):
        self.assertIsNone(validate_is_list_of_str(["1", "2"]))

    def test_rejects_a_value_that_is_not_a_list_of_strings(self):
        with self.assertRaises(ValidationError):
            validate_is_list_of_str("1")

        with self.assertRaises(ValidationError):
            validate_is_list_of_str([1])

    def test_full_clean_rejects_an_invalid_status(self):
        item = DjangoPlanItem(
            session_id="session",
            plan_id="1",
            content="Write the docs",
            status="sleeping",
            active_form="Writing the docs",
        )

        with self.assertRaises(ValidationError):
            item.full_clean()
