from django.contrib import admin

from .models import (
    Agent,
    AgentPersonality,
    AIModel,
    AIProvider,
    GoogleAIModel,
    GoogleAIProvider,
    OpenAIAIProvider,
    OpenAIModel,
    Profile,
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
        "webfetch_enabled",
        "tavily_enabled",
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


@admin.register(GoogleAIProvider)
class GoogleAIProviderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


@admin.register(OpenAIAIProvider)
class OpenAIAIProviderAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")


@admin.register(GoogleAIModel)
class GoogleAIModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")


@admin.register(OpenAIModel)
class OpenAIModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "provider", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "provider__name", "name")
