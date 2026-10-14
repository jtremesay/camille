from django.contrib import admin

from ..models import Profile


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
