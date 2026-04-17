from django.contrib import admin

from camille import models


@admin.register(models.MattermostBinding)
class MattermostBindingAdmin(admin.ModelAdmin):
    list_display = ("user", "mm_id")
