from django.contrib import admin

from .models import Agent, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "created_at", "updated_at")
    search_fields = ("uuid", "user__username")


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "slug", "name", "created_at", "updated_at")
    search_fields = ("uuid", "user__username", "slug", "name")
