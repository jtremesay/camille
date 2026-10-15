from typing import cast

from pydantic_ai_harness.planning import (
    PlanEventEmitter,
    PlanItem,
    PlanStore,
    TaskStatus,
)
from pydantic_ai_harness.planning._store import (
    emit_created,
    emit_deleted,
    emit_mutation,
)

from .models.planning import DjangoPlanItem


class DjangoPlanStore(PlanStore):
    def __init__(self, session_id: str, event_emitter: PlanEventEmitter | None = None):
        super().__init__()
        self._session_id = session_id
        self._emitter = event_emitter

    async def get_items(self) -> list[PlanItem]:
        return [
            cast(DjangoPlanItem, item).pai()
            async for item in DjangoPlanItem.objects.session(self._session_id).order_by(
                "id"
            )
        ]

    async def set_items(self, items: list[PlanItem]) -> None:
        await DjangoPlanItem.objects.aset_from_pai(self._session_id, items)

    async def get_item(self, item_id: str) -> PlanItem | None:
        try:
            item = cast(
                DjangoPlanItem,
                await DjangoPlanItem.objects.session(self._session_id).aget(
                    plan_id=item_id
                ),
            )
        except DjangoPlanItem.DoesNotExist:
            return None

        return item.pai()

    async def add_item(self, item: PlanItem) -> PlanItem:
        await DjangoPlanItem.objects.acreate_from_pai(self._session_id, item)
        await emit_created(self._emitter, item)

        return item

    async def update_item(
        self,
        item_id: str,
        *,
        content: str | None = None,
        status: TaskStatus | None = None,
        active_form: str | None = None,
        parent_id: str | None = None,
        depends_on: list[str] | None = None,
    ) -> PlanItem | None:
        try:
            item = cast(
                DjangoPlanItem,
                await DjangoPlanItem.objects.session(self._session_id).aget(
                    plan_id=item_id
                ),
            )
        except DjangoPlanItem.DoesNotExist:
            return None
        previous = item.pai() if self._emitter is not None else None

        if content is not None:
            item.content = content

        if status is not None:
            item.status = status

        if active_form is not None:
            item.active_form = active_form

        if parent_id is not None:
            item.parent_id = parent_id

        if depends_on is not None:
            item.depends_on = depends_on

        await item.asave()

        updated = item.pai()

        await emit_mutation(
            self._emitter, updated, previous
        ) if self._emitter is not None else None

        return updated

    async def remove_item(self, item_id: str) -> bool:
        item = (await self.get_item(item_id)) if self._emitter is not None else None
        deleted = (
            await DjangoPlanItem.objects.session(self._session_id)
            .filter(plan_id=item_id)
            .adelete()
        )[0] > 0
        if item is not None and deleted:
            await emit_deleted(self._emitter, item)

        return deleted
