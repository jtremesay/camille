from django.contrib import admin

from ..models import ExaApiKey


@admin.register(ExaApiKey)
class ExaApiKeyAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")
