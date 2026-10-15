from django.contrib import admin

from ..models.memory import DjangoMemoryFile, DjangoMemoryOperation


@admin.register(DjangoMemoryFile)
class DjangoMemoryFileAdmin(admin.ModelAdmin):
    list_display = ("path", "version", "last_operation_id")


@admin.register(DjangoMemoryOperation)
class DjangoMemoryOperationAdmin(admin.ModelAdmin):
    list_display = ("id", "fingerprint", "version", "existed")
