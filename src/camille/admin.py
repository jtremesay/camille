from django.contrib import admin

from .models import AIProvider


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at", "deleted_at")
    search_fields = ("name", "user__username")
