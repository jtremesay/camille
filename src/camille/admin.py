from django.contrib import admin

from . import models


class UserAWSBedrockInferenceProviderCredentialsInline(admin.StackedInline):
    model = models.UserAWSBedrockInferenceProviderCredentials
    extra = 0


class UserGoogleGLAInferenceProviderCredentialsInline(admin.StackedInline):
    model = models.UserGoogleGLAInferenceProviderCredentials
    extra = 0


class UserMistralAIInferenceProviderCredentialsInline(admin.StackedInline):
    model = models.UserMistralAIInferenceProviderCredentials
    extra = 0


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    inlines = [
        UserAWSBedrockInferenceProviderCredentialsInline,
        UserGoogleGLAInferenceProviderCredentialsInline,
        UserMistralAIInferenceProviderCredentialsInline,
    ]


@admin.register(models.UserAWSBedrockInferenceProviderCredentials)
class UserAWSBedrockInferenceProviderCredentialsAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "region_name")


@admin.register(models.UserGoogleGLAInferenceProviderCredentials)
class UserGoogleGLAInferenceProviderCredentialsAdmin(admin.ModelAdmin):
    list_display = ("id", "profile")


@admin.register(models.UserMistralAIInferenceProviderCredentials)
class UserMistralAIInferenceProviderCredentialsAdmin(admin.ModelAdmin):
    list_display = ("id", "profile")
