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


@admin.register(models.MattermostServer)
class MattermostServerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url")


@admin.register(models.MattermostTeam)
class MattermostTeamAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "server",
        "team_id",
        "name",
        "display_name",
        "create_at",
        "update_at",
    )
    search_fields = ("team_id", "name", "display_name")


@admin.register(models.MattermostUser)
class MattermostUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "server",
        "user_id",
        "username",
        "nickname",
        "first_name",
        "last_name",
        "create_at",
        "update_at",
    )
    search_fields = ("user_id", "username", "nickname", "first_name", "last_name")


@admin.register(models.MattermostTeamMember)
class MattermostTeamMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "team__server",
        "team",
        "user",
    )
    search_fields = ("team__name", "user__username")
    list_filter = ("user",)


@admin.register(models.MattermostChannel)
class MattermostChannelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "team__server",
        "team",
        "channel_id",
        "type",
        "name",
        "display_name",
        "last_post_at",
        "create_at",
        "update_at",
    )
    search_fields = ("channel_id", "type", "name", "display_name")


@admin.register(models.MattermostChannelMember)
class MattermostChannelMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "channel__team__server",
        "channel__team",
        "channel",
        "user",
    )
    search_fields = ("channel__name", "user__username")
    list_filter = ("channel", "user")


@admin.register(models.ProfileMattermostMapping)
class ProfileMattermostMappingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "profile",
        "mm_user__server",
        "mm_user",
    )
    search_fields = (
        "profile",
        "mm_user__server__name",
        "mm_user",
    )
    list_filter = ("profile", "mm_user")
