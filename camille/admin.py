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
