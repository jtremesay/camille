from django.contrib import admin

from ..models import Agent, AgentPersonality


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "user",
        "name",
        "model",
        "personality",
        "codemode_enabled",
        "memory_enabled",
        "ddg_enabled",
        "exa_enabled",
        "exa_api_key",
        "tavily_enabled",
        "tavily_api_key",
        "webfetch_enabled",
        "imgen_enabled",
        "imgen_model",
        "planning_enabled",
        "sub_agents_enabled",
        "created_at",
        "updated_at",
    )
    search_fields = ("uuid", "user__username", "name")


@admin.register(AgentPersonality)
class AgentPersonalityAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "name")
