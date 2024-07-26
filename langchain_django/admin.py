from django.contrib import admin

from langchain_django.models import *


@admin.register(DjCheckpoint)
class DjCheckpointAdmin(admin.ModelAdmin):
    list_display = (
        "thread_id",
        "thread_ts",
        "parent_ts",
        "checkpoint",
        "metadata",
    )


@admin.register(DjWrite)
class DjWriteAdmin(admin.ModelAdmin):
    list_display = (
        "thread_id",
        "thread_ts",
        "task_id",
        "idx",
        "channel",
        "value",
    )
