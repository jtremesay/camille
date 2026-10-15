from django.contrib import admin

from ..models.planning import DjangoPlanItem


@admin.register(DjangoPlanItem)
class DjangoPlanItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_id",
        "plan_id",
        "content",
        "status",
        "active_form",
        "parent_id",
        "depends_on",
    )
