from typing import Any, AsyncIterator, Dict, Iterator, List, Tuple

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, CheckpointTuple

from langchain_django.models import DjCheckpoint, DjWrite


class DjangoSaver(BaseCheckpointSaver):
    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts")

        dj_checkpoint = DjCheckpoint.objects.filter(thread_id=thread_id).values_list(
            "checkpoint", "metadata", "thread_ts", "parent_ts"
        )
        if thread_ts:
            # SELECT checkpoint, metadata, thread_ts, parent_ts
            # FROM checkpoints
            # WHERE thread_id = %(thread_id)s AND thread_ts = %(thread_ts)s
            dj_checkpoint = dj_checkpoint.filter(thread_ts=thread_ts)
        else:
            # SELECT checkpoint, metadata, thread_ts, parent_ts
            # FROM checkpoints
            # WHERE thread_id = %(thread_id)s
            # ORDER BY thread_ts DESC LIMIT 1
            dj_checkpoint = dj_checkpoint.order_by("-thread_ts")
        dj_checkpoint = dj_checkpoint.first()

        if dj_checkpoint:
            checkpoint, metadata, thread_ts, parent_ts = dj_checkpoint
            if not config["configurable"].get("thread_ts"):
                config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "thread_ts": thread_ts,
                    }
                }

                # SELECT task_id, channel, value
                # FROM writes
                # WHERE thread_id = %(thread_id)s AND thread_ts = %(thread_ts)s
                return CheckpointTuple(
                    config=config,
                    checkpoint=self.serde.loads(checkpoint),
                    metadata=self.serde.loads(metadata),
                    parent_config=(
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "thread_ts": parent_ts,
                            }
                        }
                        if parent_ts
                        else None
                    ),
                    pending_writes=[
                        (task_id, channel, self.serde.loads(value))
                        for task_id, channel, value in DjWrite.objects.filter(
                            thread_id=thread_id, thread_ts=thread_ts
                        ).values_list("task_id", "channel", "value")
                    ],
                )

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts")

        dj_checkpoint = DjCheckpoint.objects.filter(thread_id=thread_id).values_list(
            "checkpoint", "metadata", "thread_ts", "parent_ts"
        )
        if thread_ts:
            # SELECT checkpoint, metadata, thread_ts, parent_ts
            # FROM checkpoints
            # WHERE thread_id = %(thread_id)s AND thread_ts = %(thread_ts)s
            dj_checkpoint = dj_checkpoint.filter(thread_ts=thread_ts)
        else:
            # SELECT checkpoint, metadata, thread_ts, parent_ts
            # FROM checkpoints
            # WHERE thread_id = %(thread_id)s
            # ORDER BY thread_ts DESC LIMIT 1
            dj_checkpoint = dj_checkpoint.order_by("-thread_ts")
        dj_checkpoint = await dj_checkpoint.afirst()

        if dj_checkpoint:
            checkpoint, metadata, thread_ts, parent_ts = dj_checkpoint
            if not config["configurable"].get("thread_ts"):
                config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "thread_ts": thread_ts,
                    }
                }

                # SELECT task_id, channel, value
                # FROM writes
                # WHERE thread_id = %(thread_id)s AND thread_ts = %(thread_ts)s
                return CheckpointTuple(
                    config=config,
                    checkpoint=self.serde.loads(checkpoint),
                    metadata=self.serde.loads(metadata),
                    parent_config=(
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "thread_ts": parent_ts,
                            }
                        }
                        if parent_ts
                        else None
                    ),
                    pending_writes=[
                        (task_id, channel, self.serde.loads(value))
                        async for task_id, channel, value in DjWrite.objects.filter(
                            thread_id=thread_id, thread_ts=thread_ts
                        ).values_list("task_id", "channel", "value")
                    ],
                )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: Dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None
    ) -> Iterator[CheckpointTuple]:
        checkpoints = (
            DjCheckpoint.objects.all()
            .order_by("-thread_ts")
            .values_list("checkpoint", "metadata", "thread_ts", "parent_ts")
        )
        if config:
            checkpoints = checkpoints.filter(
                thread_id=config["configurable"]["thread_id"]
            )

        if filter:
            raise NotImplementedError("Filtering not implemented")

        if before:
            checkpoints = checkpoints.filter(
                thread_ts__lt=before["configurable"]["thread_ts"]
            )

        if limit:
            checkpoints = checkpoints[:limit]

        thread_id = config["configurable"]["thread_id"]
        for checkpoint, metadata, thread_ts, parent_ts in checkpoints:
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "thread_ts": thread_ts,
                    }
                },
                checkpoint=self.serde.loads(checkpoint),
                metadata=self.serde.loads(metadata),
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "thread_ts": thread_ts,
                        }
                    }
                    if parent_ts
                    else None
                ),
            )

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: Dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None
    ) -> AsyncIterator[CheckpointTuple]:
        checkpoints = (
            DjCheckpoint.objects.all()
            .order_by("-thread_ts")
            .values_list("checkpoint", "metadata", "thread_ts", "parent_ts")
        )
        if config:
            checkpoints = checkpoints.filter(
                thread_id=config["configurable"]["thread_id"]
            )

        if filter:
            raise NotImplementedError("Filtering not implemented")

        if before:
            checkpoints = checkpoints.filter(
                thread_ts__lt=before["configurable"]["thread_ts"]
            )

        if limit:
            checkpoints = checkpoints[:limit]

        thread_id = config["configurable"]["thread_id"]
        async for checkpoint, metadata, thread_ts, parent_ts in checkpoints:
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "thread_ts": thread_ts,
                    }
                },
                checkpoint=self.serde.loads(checkpoint),
                metadata=self.serde.loads(metadata),
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "thread_ts": thread_ts,
                        }
                    }
                    if parent_ts
                    else None
                ),
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        parent_ts = config["configurable"].get("thread_ts")
        DjCheckpoint.objects.update_or_create(
            thread_id=thread_id,
            thread_ts=checkpoint["id"],
            defaults={
                "parent_ts": parent_ts if parent_ts else None,
                "checkpoint": self.serde.dumps(checkpoint),
                "metadata": self.serde.dumps(metadata),
            },
        )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        parent_ts = config["configurable"].get("thread_ts")
        await DjCheckpoint.objects.aupdate_or_create(
            thread_id=thread_id,
            thread_ts=checkpoint["id"],
            defaults={
                "parent_ts": parent_ts if parent_ts else None,
                "checkpoint": self.serde.dumps(checkpoint),
                "metadata": self.serde.dumps(metadata),
            },
        )

    def put_writes(
        self, config: RunnableConfig, writes: List[Tuple[str, Any]], task_id: str
    ) -> None:
        # INSERT INTO writes
        #     (thread_id, thread_ts, task_id, idx, channel, value)
        # VALUES
        #     (%s, %s, %s, %s, %s, %s)
        # ON CONFLICT (thread_id, thread_ts, task_id, idx)
        # DO UPDATE SET value = EXCLUDED.value;
        DjWrite.objects.bulk_create(
            [
                DjWrite(
                    thread_id=config["configurable"]["thread_id"],
                    thread_ts=config["configurable"]["thread_ts"],
                    task_id=task_id,
                    idx=idx,
                    channel=channel,
                    value=self.serde.dumps(value),
                )
                for idx, (channel, value) in enumerate(writes)
            ],
            ignore_conflicts=False,
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["thread_id", "thread_ts", "task_id", "idx"],
        )

    async def aput_writes(
        self, config: RunnableConfig, writes: List[Tuple[str | Any]], task_id: str
    ) -> None:
        # INSERT INTO writes
        #     (thread_id, thread_ts, task_id, idx, channel, value)
        # VALUES
        #     (%s, %s, %s, %s, %s, %s)
        # ON CONFLICT (thread_id, thread_ts, task_id, idx)
        # DO UPDATE SET value = EXCLUDED.value;
        await DjWrite.objects.abulk_create(
            [
                DjWrite(
                    thread_id=config["configurable"]["thread_id"],
                    thread_ts=config["configurable"]["thread_ts"],
                    task_id=task_id,
                    idx=idx,
                    channel=channel,
                    value=self.serde.dumps(value),
                )
                for idx, (channel, value) in enumerate(writes)
            ],
            ignore_conflicts=False,
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["thread_id", "thread_ts", "task_id", "idx"],
        )
