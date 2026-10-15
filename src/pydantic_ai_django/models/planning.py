from typing import cast

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from pydantic_ai_harness.planning import PlanItem, TaskStatus


def task_status_len() -> int:
    return max(len(status.value) for status in TaskStatus)


def validate_is_task_status(value):
    try:
        TaskStatus(value)
    except ValueError:
        raise ValidationError(f"Value '{value}' is not a valid TaskStatus.")


def validate_is_list_of_str(value):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValidationError(f"Value '{value}' is not a valid list of strings.")


class DjangoPlanItemManager(models.Manager):
    def session(self, session_id: str) -> QuerySet:
        return self.filter(session_id=session_id)

    async def acreate_from_pai(self, session_id: str, item: PlanItem) -> DjangoPlanItem:
        return await DjangoPlanItem.objects.acreate(
            session_id=session_id,
            plan_id=item.id,
            content=item.content,
            status=item.status,
            active_form=item.active_form,
            parent_id=item.parent_id,
            depends_on=item.depends_on,
        )

    async def aset_from_pai(self, session_id: str, items: list[PlanItem]) -> None:
        await DjangoPlanItem.objects.session(session_id).adelete()
        await DjangoPlanItem.objects.abulk_create(
            [
                DjangoPlanItem(
                    session_id=session_id,
                    plan_id=item.id,
                    content=item.content,
                    status=item.status,
                    active_form=item.active_form,
                    parent_id=item.parent_id,
                    depends_on=item.depends_on,
                )
                for item in items
            ]
        )


class DjangoPlanItem(models.Model):
    objects = DjangoPlanItemManager()

    session_id = models.TextField()
    plan_id = models.TextField()
    content = models.TextField()
    status = models.CharField(
        max_length=task_status_len(), validators=[validate_is_task_status]
    )
    active_form = models.TextField()
    parent_id = models.TextField(null=True, blank=True)
    depends_on = models.JSONField(default=list, validators=[validate_is_list_of_str])

    class Meta:
        unique_together = ("session_id", "plan_id")

    def pai(self) -> PlanItem:
        return PlanItem(
            id=cast(str, self.plan_id),
            content=cast(str, self.content),
            status=self.status,
            active_form=cast(str, self.active_form),
            parent_id=cast(str | None, self.parent_id),
            depends_on=cast(list[str], self.depends_on),
        )
