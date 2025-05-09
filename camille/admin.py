from django.contrib import admin

from camille.models import MMChannel, MMMembership, MMTeam, MMUser


@admin.register(MMTeam)
class MMTeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "display_name")


class MembershipInline(admin.TabularInline):
    model = MMMembership
    extra = 0


@admin.register(MMChannel)
class MMChannelAdmin(admin.ModelAdmin):
    list_display = ("id", "team__name", "type", "name", "display_name")
    inlines = [MembershipInline]


@admin.register(MMUser)
class MMUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "nickname", "first_name", "last_name")
    inlines = [MembershipInline]
