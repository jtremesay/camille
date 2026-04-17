from django.contrib import admin

from camille import models


@admin.register(models.MattermostBinding)
class MattermostBindingAdmin(admin.ModelAdmin):
    list_display = ("user", "mm_id")


@admin.register(models.AgentPersonality)
class AgentPersonalityAdmin(admin.ModelAdmin):
    list_display = ("user", "name")
    list_filter = ("user",)
