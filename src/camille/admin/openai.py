from django.contrib import admin

from ..models import OpenAIAIProvider, OpenAIImageModel, OpenAIModel


@admin.register(OpenAIAIProvider)
class OpenAIAIProviderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


@admin.register(OpenAIModel)
class OpenAIModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")


@admin.register(OpenAIImageModel)
class OpenAIImageModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")
