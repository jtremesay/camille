from django.contrib import admin

from camille_orgs import models


class TeamToOrganizationInline(admin.TabularInline):
    model = models.TeamToOrganization
    extra = 1


class UserToOrganizationInline(admin.TabularInline):
    model = models.UserToOrganization
    extra = 1


class UserToTeamInline(admin.TabularInline):
    model = models.UserToTeam
    extra = 1


# Register your models here.
@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("uuid", "name", "slug", "created_at", "updated_at")
    inlines = [TeamToOrganizationInline, UserToOrganizationInline]


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("uuid", "name", "slug", "created_at", "updated_at")
    inlines = [UserToTeamInline]


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "created_at", "updated_at")
