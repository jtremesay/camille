from django.contrib import admin

from camille import models


# Register your models here.
@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "model_name", "personality")


@admin.register(models.BedrockCredentials)
class BedrockCredentialsAdmin(admin.ModelAdmin):
    list_display = ("profile", "region")


@admin.register(models.GoogleGLACredentials)
class GoogleGLACredentialsAdmin(admin.ModelAdmin):
    list_display = ("profile",)


@admin.register(models.MistralAICredentials)
class MistralAICredentialsAdmin(admin.ModelAdmin):
    list_display = ("profile",)


@admin.register(models.AgentPersonality)
class AgentPersonalityAdmin(admin.ModelAdmin):
    list_display = ("owner", "name", "description")
