from django.contrib import admin

from ..models import AIImageModel, AIModel, AIProvider


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")


@admin.register(AIImageModel)
class AIImageModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")
