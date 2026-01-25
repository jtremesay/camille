from django.contrib import admin

from camille.models import (
    MMChannel,
    MMInteraction,
    MMMembership,
    MMTeam,
    MMThread,
    MMUser,
    PersonalityPrompt,
)


@admin.register(MMTeam)
class MMTeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "display_name")


class MembershipInline(admin.TabularInline):
    model = MMMembership
    extra = 0


class ThreadInline(admin.TabularInline):
    model = MMThread
    extra = 0


@admin.register(MMChannel)
class MMChannelAdmin(admin.ModelAdmin):
    list_display = ("id", "team__name", "type", "name", "display_name", "notes")
    inlines = [MembershipInline, ThreadInline]


@admin.register(MMUser)
class MMUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "nickname", "first_name", "last_name", "notes")
    inlines = [MembershipInline]


class InteractionInline(admin.TabularInline):
    model = MMInteraction
    extra = 0


@admin.register(MMThread)
class MMThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "channel__name", "created_at")
    list_filter = ("channel__team__name", "channel__name")
    ordering = ("-created_at",)
    inlines = [InteractionInline]


@admin.register(MMInteraction)
class MMInteractionAdmin(admin.ModelAdmin):
    list_display = ("id", "thread__channel__name", "thread__created_at", "created_at")
    list_filter = ("thread__channel__team__name", "thread__channel__name")
    ordering = ("-created_at",)


@admin.register(PersonalityPrompt)
class PersonalityPromptAdmin(admin.ModelAdmin):
    list_display = ("id", "user__username", "name", "description")
