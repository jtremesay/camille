from django.contrib import admin

from camille import models


@admin.register(models.MattermostBinding)
class MattermostBindingAdmin(admin.ModelAdmin):
    list_display = ("user", "mm_id")
    search_fields = ("user__username", "mm_id")


@admin.register(models.AgentPersonality)
class AgentPersonalityAdmin(admin.ModelAdmin):
    list_display = ("user", "name")
    list_filter = ("user__username",)
    search_fields = ("user__username", "name")


@admin.register(models.AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "model", "personality")
    list_filter = ("user__username", "model")
    search_fields = ("user__username", "model", "personality__name")


@admin.register(models.AnthropicCredentials)
class AnthropicCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)


@admin.register(models.AWSBedrockCredentials)
class AWSBedrockCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user", "region_name")
    list_filter = ("user__username",)


@admin.register(models.GoogleGLACredentials)
class GoogleGLACredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)


@admin.register(models.MistralCredentials)
class MistralCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)


@admin.register(models.OpenRouterCredentials)
class OpenRouterCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)
