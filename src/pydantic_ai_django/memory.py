from typing import cast

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from django.db.models import CharField
from django.db.models.functions import Cast, Length, Substr
from pydantic_ai_harness.memory import (
    MemoryConflictError,
    MemoryFile,
    MemoryMutation,
    MemoryOperation,
    MemoryOperationConflictError,
    MemorySearchResult,
    SearchableMemoryStore,
)
from pydantic_ai_harness.memory._store import (
    lexical_search,
    validate_store_path,
    validate_store_prefix,
)

from pydantic_ai_django.models.memory import (
    DjangoMemoryFile,
    DjangoMemoryGeneration,
    DjangoMemoryOperation,
)


class DjangoMemoryStore(SearchableMemoryStore):
    async def read(self, path: str, *, max_chars: int) -> MemoryFile | None:
        validate_store_path(path)
        if max_chars <= 0:
            raise ValueError("max_chars must be greater than 0")

        value = cast(
            tuple[str, int, str | None, int] | None,
            await DjangoMemoryFile.objects.filter(path=path)
            .values_list(
                Substr("content", 1, max_chars),
                "version",
                "last_operation_id",
                Length("content"),
            )
            .afirst(),
        )
        if value is None:
            return None

        return MemoryFile(
            content=value[0],
            version=str(value[1]),
            operation_id=value[2],
            truncated=value[3] > max_chars,
        )

    async def get_operation(self, operation: MemoryOperation) -> MemoryMutation | None:
        value: tuple[str, str | None, bool] | None = (
            await DjangoMemoryOperation.objects.filter(id=operation.id)
            .values_list("fingerprint", "version", "existed")
            .afirst()
        )
        if value is None:
            return None

        if value[0] != operation.fingerprint:
            raise MemoryOperationConflictError(
                f"operation id {operation.id!r} was reused with different arguments"
            )

        return MemoryMutation(version=value[1], replayed=True, existed=value[2])

    @staticmethod
    def _get_operation_sync(operation: MemoryOperation) -> MemoryMutation | None:
        value = (
            DjangoMemoryOperation.objects.filter(id=operation.id)
            .values_list("fingerprint", "version", "existed")
            .first()
        )
        if value is None:
            return None

        if value[0] != operation.fingerprint:
            raise MemoryOperationConflictError(
                f"operation id {operation.id!r} was reused with different arguments"
            )

        return MemoryMutation(version=value[1], replayed=True, existed=value[2])

    @staticmethod
    def _version_filter(expected_version: str):
        return DjangoMemoryFile.objects.annotate(
            version_string=Cast("version", output_field=CharField())
        ).filter(version_string=expected_version)

    def _write_sync(
        self,
        path: str,
        content: str,
        expected_version: str | None,
        operation: MemoryOperation | None,
    ) -> MemoryMutation:
        try:
            with transaction.atomic():
                if (
                    operation is not None
                    and (receipt := self._get_operation_sync(operation)) is not None
                ):
                    return receipt

                version = DjangoMemoryGeneration.objects.create().pk
                if expected_version is None:
                    DjangoMemoryFile.objects.create(
                        path=path,
                        content=content,
                        version=version,
                        last_operation_id=operation.id
                        if operation is not None
                        else None,
                    )
                    existed = False
                else:
                    updated = (
                        self._version_filter(expected_version)
                        .filter(path=path)
                        .update(
                            content=content,
                            version=version,
                            last_operation_id=operation.id
                            if operation is not None
                            else None,
                        )
                    )
                    if updated != 1:
                        raise MemoryConflictError(
                            f"memory path {path!r} changed before it could be written"
                        )
                    existed = True

                mutation = MemoryMutation(
                    version=str(version),
                    replayed=False,
                    existed=existed,
                )
                if operation is not None:
                    DjangoMemoryOperation.objects.create(
                        id=operation.id,
                        fingerprint=operation.fingerprint,
                        version=mutation.version,
                        existed=existed,
                    )
                return mutation
        except IntegrityError:
            if (
                operation is not None
                and (receipt := self._get_operation_sync(operation)) is not None
            ):
                return receipt
            if (
                expected_version is None
                and DjangoMemoryFile.objects.filter(path=path).exists()
            ):
                raise MemoryConflictError(
                    f"memory path {path!r} changed before it could be written"
                ) from None
            raise

    async def write(
        self,
        path: str,
        content: str,
        *,
        expected_version: str | None,
        operation: MemoryOperation | None = None,
    ) -> MemoryMutation:
        validate_store_path(path)
        return await sync_to_async(self._write_sync, thread_sensitive=True)(
            path, content, expected_version, operation
        )

    def _delete_sync(
        self,
        path: str,
        expected_version: str | None,
        operation: MemoryOperation | None,
    ) -> MemoryMutation:
        try:
            with transaction.atomic():
                if (
                    operation is not None
                    and (receipt := self._get_operation_sync(operation)) is not None
                ):
                    return receipt

                DjangoMemoryGeneration.objects.create()
                if expected_version is None:
                    if DjangoMemoryFile.objects.filter(path=path).exists():
                        raise MemoryConflictError(
                            f"memory path {path!r} changed before it could be deleted"
                        )
                    existed = False
                else:
                    deleted, _ = (
                        self._version_filter(expected_version)
                        .filter(path=path)
                        .delete()
                    )
                    if deleted != 1:
                        raise MemoryConflictError(
                            f"memory path {path!r} changed before it could be deleted"
                        )
                    existed = True

                mutation = MemoryMutation(version=None, replayed=False, existed=existed)
                if operation is not None:
                    DjangoMemoryOperation.objects.create(
                        id=operation.id,
                        fingerprint=operation.fingerprint,
                        version=None,
                        existed=existed,
                    )
                return mutation
        except IntegrityError:
            if (
                operation is not None
                and (receipt := self._get_operation_sync(operation)) is not None
            ):
                return receipt
            raise

    async def delete(
        self,
        path: str,
        *,
        expected_version: str | None,
        operation: MemoryOperation | None = None,
    ) -> MemoryMutation:
        validate_store_path(path)
        return await sync_to_async(self._delete_sync, thread_sensitive=True)(
            path, expected_version, operation
        )

    @staticmethod
    def _prefix_queryset(prefix: str):
        queryset = DjangoMemoryFile.objects.all()
        if prefix:
            queryset = queryset.annotate(
                _memory_path_prefix=Substr("path", 1, len(prefix))
            ).filter(_memory_path_prefix=prefix)
        return queryset

    async def list_paths(self, prefix: str = "", *, limit: int) -> list[str]:
        validate_store_prefix(prefix)
        if limit <= 0:
            raise ValueError("limit must be positive")

        return [
            path
            async for path in self._prefix_queryset(prefix)
            .order_by("path")
            .values_list("path", flat=True)[:limit]
        ]

    async def search(
        self,
        prefix: str,
        query: str,
        *,
        limit: int,
        max_files: int,
        max_chars: int,
        max_file_chars: int,
    ) -> MemorySearchResult:
        validate_store_prefix(prefix)
        if (
            not query.split()
            or limit <= 0
            or max_files <= 0
            or max_chars <= 0
            or max_file_chars <= 0
        ):
            return MemorySearchResult(matches=[], scanned=0, truncated=False)

        values: list[tuple[str, str, int]] = [
            row
            async for row in self._prefix_queryset(prefix)
            .order_by("path")
            .values_list(
                "path", Substr("content", 1, max_file_chars), Length("content")
            )[: max_files + 1]
        ]
        result = lexical_search(
            ((path, content) for path, content, _ in values),
            query=query,
            limit=limit,
            max_files=max_files,
            max_chars=max_chars,
            score_prefix=prefix,
        )

        return MemorySearchResult(
            matches=result.matches,
            scanned=result.scanned,
            truncated=result.truncated
            or any(content_len > max_file_chars for _, _, content_len in values),
        )
