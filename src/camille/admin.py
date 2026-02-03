from django.contrib import admin

from camille import models


class UserCredentialsInline(admin.TabularInline):
    model = models.UserCredentials
    extra = 1
    raw_id_fields = ("credentials",)


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username", "user__email")
    inlines = [UserCredentialsInline]


@admin.register(models.AwsBedrockCredentials)
class AwsBedrockCredentialsAdmin(admin.ModelAdmin):
    list_display = ("name", "region_name", "api_key_preview")
    search_fields = ("name", "region_name")
    list_filter = ("region_name",)

    def api_key_preview(self, obj):
        """Show only the first few characters of the API key for security."""
        if obj.api_key:
            return f"{obj.api_key[:8]}..." if len(obj.api_key) > 8 else obj.api_key
        return ""


@admin.register(models.GoogleGlaCredentials)
class GoogleGlaCredentialsAdmin(admin.ModelAdmin):
    list_display = ("name", "api_key_preview")
    search_fields = ("name",)

    def api_key_preview(self, obj):
        """Show only the first few characters of the API key for security."""
        if obj.api_key:
            return f"{obj.api_key[:8]}..." if len(obj.api_key) > 8 else obj.api_key
        return ""


@admin.register(models.MistralCredentials)
class MistralCredentialsAdmin(admin.ModelAdmin):
    list_display = ("name", "api_key_preview")
    search_fields = ("name",)

    def api_key_preview(self, obj):
        """Show only the first few characters of the API key for security."""
        if obj.api_key:
            return f"{obj.api_key[:8]}..." if len(obj.api_key) > 8 else obj.api_key
        return ""


@admin.register(models.UserCredentials)
class UserCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user_profile", "credentials")
    search_fields = ("user_profile__user__username", "credentials__name")
    raw_id_fields = ("user_profile", "credentials")


@admin.register(models.MattermostServer)
class MattermostServerAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "api_token_preview")
    search_fields = ("name", "base_url")

    def api_token_preview(self, obj):
        """Show only the first few characters of the API token for security."""
        if obj.api_token:
            return (
                f"{obj.api_token[:8]}..." if len(obj.api_token) > 8 else obj.api_token
            )
        return ""


@admin.register(models.MattermostTeam)
class MattermostTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "server")
    search_fields = ("name", "display_name", "team_id")
    list_filter = ("server",)
    raw_id_fields = ("server",)


@admin.register(models.MattermostChannel)
class MattermostChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "kind", "team")
    search_fields = ("name", "display_name", "channel_id")
    list_filter = ("kind", "team")
    raw_id_fields = ("team",)


@admin.register(models.MattermostUser)
class MattermostUserAdmin(admin.ModelAdmin):
    list_display = ("username", "display_name", "user_id", "server")
    search_fields = ("username", "display_name", "user_id")
    list_filter = ("server",)
    raw_id_fields = ("server",)


@admin.register(models.MattermostChannelMember)
class MattermostChannelMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "channel")
    search_fields = ("user__username", "channel__name")
    list_filter = ("channel__team__server",)
    raw_id_fields = ("channel", "user")
