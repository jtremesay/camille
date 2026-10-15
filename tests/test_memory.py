from unittest import mock

from asgiref.sync import async_to_sync
from django.db import IntegrityError
from django.test import TestCase
from pydantic_ai_harness.memory import (
    MemoryConflictError,
    MemoryMutation,
    MemoryOperation,
    MemoryOperationConflictError,
)

from pydantic_ai_django.memory import DjangoMemoryStore
from pydantic_ai_django.models.memory import DjangoMemoryFile


class DjangoMemoryStoreTests(TestCase):
    def setUp(self):
        self.store = DjangoMemoryStore()

    def test_write_update_delete_and_recreate_use_compare_and_set_versions(self):
        first = async_to_sync(self.store.write)(
            "notes/todo.md",
            "first",
            expected_version=None,
        )
        self.assertFalse(first.existed)
        self.assertEqual(first.version, "1")

        second = async_to_sync(self.store.write)(
            "notes/todo.md",
            "second",
            expected_version=first.version,
        )
        self.assertTrue(second.existed)
        self.assertNotEqual(second.version, first.version)
        self.assertEqual(
            async_to_sync(self.store.read)("notes/todo.md", max_chars=20).content,
            "second",
        )

        with self.assertRaises(MemoryConflictError):
            async_to_sync(self.store.write)(
                "notes/todo.md",
                "stale",
                expected_version=first.version,
            )

        deleted = async_to_sync(self.store.delete)(
            "notes/todo.md",
            expected_version=second.version,
        )
        self.assertTrue(deleted.existed)
        self.assertIsNone(async_to_sync(self.store.read)("notes/todo.md", max_chars=20))

        recreated = async_to_sync(self.store.write)(
            "notes/todo.md",
            "third",
            expected_version=None,
        )
        self.assertGreater(int(recreated.version), int(second.version))
        with self.assertRaises(MemoryConflictError):
            async_to_sync(self.store.write)(
                "notes/todo.md",
                "stale create",
                expected_version=None,
            )

    def test_operation_receipts_replay_writes_and_deletes(self):
        write_operation = MemoryOperation(id="write-1", fingerprint="write-fingerprint")
        written = async_to_sync(self.store.write)(
            "notes/receipt.md",
            "saved",
            expected_version=None,
            operation=write_operation,
        )
        replayed_write = async_to_sync(self.store.write)(
            "notes/receipt.md",
            "ignored",
            expected_version="stale",
            operation=write_operation,
        )
        self.assertEqual(replayed_write.version, written.version)
        self.assertTrue(replayed_write.replayed)
        self.assertEqual(
            async_to_sync(self.store.read)(
                "notes/receipt.md", max_chars=20
            ).operation_id,
            write_operation.id,
        )

        with self.assertRaises(MemoryOperationConflictError):
            async_to_sync(self.store.get_operation)(
                MemoryOperation(id=write_operation.id, fingerprint="different")
            )

        delete_operation = MemoryOperation(
            id="delete-1",
            fingerprint="delete-fingerprint",
        )
        deleted = async_to_sync(self.store.delete)(
            "notes/receipt.md",
            expected_version=written.version,
            operation=delete_operation,
        )
        replayed_delete = async_to_sync(self.store.delete)(
            "notes/receipt.md",
            expected_version=None,
            operation=delete_operation,
        )
        self.assertTrue(deleted.existed)
        self.assertTrue(replayed_delete.replayed)
        self.assertTrue(replayed_delete.existed)
        self.assertIsNone(replayed_delete.version)

    def test_path_listing_and_search_accept_empty_prefix_and_report_bounds(self):
        DjangoMemoryFile.objects.create(
            path="Notes/one.md", content="needle", version=1
        )
        DjangoMemoryFile.objects.create(
            path="notes/two.md", content="needle", version=2
        )

        self.assertEqual(
            async_to_sync(self.store.list_paths)(limit=10),
            ["Notes/one.md", "notes/two.md"],
        )
        self.assertEqual(
            async_to_sync(self.store.list_paths)("notes/", limit=10),
            ["notes/two.md"],
        )

        result = async_to_sync(self.store.search)(
            "",
            "needle",
            limit=10,
            max_files=1,
            max_chars=100,
            max_file_chars=100,
        )
        self.assertEqual(result.scanned, 1)
        self.assertTrue(result.truncated)


class DjangoMemoryStoreEdgeCaseTests(TestCase):
    def setUp(self):
        self.store = DjangoMemoryStore()

    def test_read_rejects_a_non_positive_max_chars(self):
        with self.assertRaisesMessage(ValueError, "max_chars must be greater than 0"):
            async_to_sync(self.store.read)("notes/todo.md", max_chars=0)

    def test_read_returns_none_for_an_unknown_path(self):
        self.assertIsNone(async_to_sync(self.store.read)("nope.md", max_chars=10))

    def test_read_reports_truncation(self):
        async_to_sync(self.store.write)(
            "notes/todo.md", "long content", expected_version=None
        )

        memory_file = async_to_sync(self.store.read)("notes/todo.md", max_chars=4)

        self.assertEqual(memory_file.content, "long")
        self.assertTrue(memory_file.truncated)

    def test_get_operation_returns_none_for_an_unknown_operation(self):
        self.assertIsNone(
            async_to_sync(self.store.get_operation)(
                MemoryOperation(id="missing", fingerprint="fingerprint")
            )
        )

    def test_get_operation_returns_the_recorded_mutation(self):
        operation = MemoryOperation(id="op-1", fingerprint="fingerprint")
        written = async_to_sync(self.store.write)(
            "notes/todo.md", "content", expected_version=None, operation=operation
        )

        mutation = async_to_sync(self.store.get_operation)(operation)

        self.assertEqual(mutation.version, written.version)
        self.assertTrue(mutation.replayed)
        self.assertFalse(mutation.existed)

    def test_delete_of_an_unknown_path_without_expected_version(self):
        mutation = async_to_sync(self.store.delete)("nope.md", expected_version=None)

        self.assertFalse(mutation.existed)
        self.assertIsNone(mutation.version)

    def test_delete_of_an_existing_path_without_expected_version_conflicts(self):
        async_to_sync(self.store.write)(
            "notes/todo.md", "content", expected_version=None
        )

        with self.assertRaises(MemoryConflictError):
            async_to_sync(self.store.delete)("notes/todo.md", expected_version=None)

    def test_delete_with_a_stale_expected_version_conflicts(self):
        async_to_sync(self.store.write)(
            "notes/todo.md", "content", expected_version=None
        )

        with self.assertRaises(MemoryConflictError):
            async_to_sync(self.store.delete)("notes/todo.md", expected_version="stale")

    def test_list_paths_rejects_a_non_positive_limit(self):
        with self.assertRaisesMessage(ValueError, "limit must be positive"):
            async_to_sync(self.store.list_paths)(limit=0)

    def test_search_returns_nothing_for_a_degenerate_query(self):
        DjangoMemoryFile.objects.create(
            path="notes/one.md", content="needle", version=1
        )

        for kwargs in (
            {"query": "   "},
            {"limit": 0},
            {"max_files": 0},
            {"max_chars": 0},
            {"max_file_chars": 0},
        ):
            arguments = {
                "query": "needle",
                "limit": 10,
                "max_files": 10,
                "max_chars": 100,
                "max_file_chars": 100,
            } | kwargs

            result = async_to_sync(self.store.search)("", **arguments)

            self.assertEqual(result.matches, [])
            self.assertEqual(result.scanned, 0)
            self.assertFalse(result.truncated)


class DjangoMemoryStoreConcurrencyTests(TestCase):
    """Recovery paths taken when another writer wins the race."""

    def setUp(self):
        self.store = DjangoMemoryStore()
        self.operation = MemoryOperation(id="op-1", fingerprint="fingerprint")
        self.receipt = MemoryMutation(version="7", replayed=True, existed=True)

    def patch_generation(self):
        return mock.patch(
            "pydantic_ai_django.memory.DjangoMemoryGeneration.objects.create",
            side_effect=IntegrityError("concurrent writer"),
        )

    def patch_receipt(self):
        """The operation is only visible once the concurrent writer committed."""
        return mock.patch.object(
            DjangoMemoryStore,
            "_get_operation_sync",
            side_effect=[None, self.receipt],
        )

    def test_write_replays_an_operation_committed_concurrently(self):
        with self.patch_generation(), self.patch_receipt():
            mutation = async_to_sync(self.store.write)(
                "notes/todo.md",
                "content",
                expected_version=None,
                operation=self.operation,
            )

        self.assertEqual(mutation, self.receipt)

    def test_write_reraises_an_unrecoverable_integrity_error(self):
        with self.patch_generation(), self.assertRaises(IntegrityError):
            async_to_sync(self.store.write)(
                "notes/todo.md", "content", expected_version="1"
            )

    def test_delete_replays_an_operation_committed_concurrently(self):
        with self.patch_generation(), self.patch_receipt():
            mutation = async_to_sync(self.store.delete)(
                "notes/todo.md",
                expected_version=None,
                operation=self.operation,
            )

        self.assertEqual(mutation, self.receipt)

    def test_delete_reraises_an_unrecoverable_integrity_error(self):
        with self.patch_generation(), self.assertRaises(IntegrityError):
            async_to_sync(self.store.delete)("notes/todo.md", expected_version="1")


class GetOperationSyncTests(TestCase):
    def test_returns_none_for_an_unknown_operation(self):
        self.assertIsNone(
            DjangoMemoryStore._get_operation_sync(
                MemoryOperation(id="missing", fingerprint="fingerprint")
            )
        )

    def test_returns_the_recorded_mutation(self):
        store = DjangoMemoryStore()
        operation = MemoryOperation(id="op-1", fingerprint="fingerprint")
        written = async_to_sync(store.write)(
            "notes/todo.md", "content", expected_version=None, operation=operation
        )

        mutation = DjangoMemoryStore._get_operation_sync(operation)

        self.assertEqual(mutation.version, written.version)
        self.assertTrue(mutation.replayed)
        self.assertFalse(mutation.existed)

    def test_rejects_an_operation_id_reused_with_other_arguments(self):
        store = DjangoMemoryStore()
        async_to_sync(store.write)(
            "notes/todo.md",
            "content",
            expected_version=None,
            operation=MemoryOperation(id="op-1", fingerprint="fingerprint"),
        )

        with self.assertRaises(MemoryOperationConflictError):
            DjangoMemoryStore._get_operation_sync(
                MemoryOperation(id="op-1", fingerprint="different")
            )
