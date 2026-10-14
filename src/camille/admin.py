from django.contrib import admin

from .models import (
    Agent,
    AgentPersonality,
    AIImageModel,
    AIModel,
    AIProvider,
    ExaApiKey,
    GoogleAIImageModel,
    GoogleAIModel,
    GoogleAIProvider,
    OpenAIAIProvider,
    OpenAIImageModel,
    OpenAIModel,
    Profile,
    TavilyApiKey,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "user",
        "default_agent",
        "default_model",
        "created_at",
        "updated_at",
    )
    search_fields = ("uuid", "user__username")


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "user",
        "name",
        "model",
        "personality",
        "ddg_enabled",
        "exa_enabled",
        "exa_api_key",
        "tavily_enabled",
        "tavily_api_key",
        "webfetch_enabled",
        "imgen_enabled",
        "imgen_model",
        "created_at",
        "updated_at",
    )
    search_fields = ("uuid", "user__username", "name")


@admin.register(AgentPersonality)
class AgentPersonalityAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


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


@admin.register(TavilyApiKey)
class TavilyApiKeyAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


@admin.register(ExaApiKey)
class ExaApiKeyAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")
