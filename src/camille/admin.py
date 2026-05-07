# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from django.contrib import admin

from camille import models


@admin.register(models.MattermostBinding)
class MattermostBindingAdmin(admin.ModelAdmin):
    list_display = ("user", "mm_id")
    search_fields = ("user__username", "mm_id")


@admin.register(models.AgentPersonality)
class AgentPersonalityAdmin(admin.ModelAdmin):
    list_display = ("user", "name")
    list_filter = ("user__username",)
    search_fields = ("user__username", "name")


@admin.register(models.AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "model", "personality")
    list_filter = ("user__username", "model")
    search_fields = ("user__username", "model", "personality__name")


@admin.register(models.AgentMemory)
class AgentMemoryAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "content")
    list_filter = ("user__username", "created_at")
    search_fields = ("user__username", "content")


@admin.register(models.AnthropicCredentials)
class AnthropicCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)


@admin.register(models.AWSBedrockCredentials)
class AWSBedrockCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user", "region_name")
    list_filter = ("user__username",)


@admin.register(models.GoogleGLACredentials)
class GoogleGLACredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)


@admin.register(models.MistralCredentials)
class MistralCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)


@admin.register(models.OpenRouterCredentials)
class OpenRouterCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user",)
    list_filter = ("user__username",)
