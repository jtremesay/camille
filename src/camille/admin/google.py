from django.contrib import admin

from ..models import GoogleAIImageModel, GoogleAIModel, GoogleAIProvider


@admin.register(GoogleAIProvider)
class GoogleAIProviderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


@admin.register(GoogleAIModel)
class GoogleAIModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")


@admin.register(GoogleAIImageModel)
class GoogleAIImageModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")
