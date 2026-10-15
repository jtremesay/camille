from asgiref.sync import async_to_sync
from django.test import TestCase
from pydantic_ai_harness.memory import (
    MemoryConflictError,
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
