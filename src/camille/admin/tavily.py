from django.contrib import admin

from ..models import TavilyApiKey


@admin.register(TavilyApiKey)
class TavilyApiKeyAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")
