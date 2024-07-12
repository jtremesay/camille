# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from django.contrib import admin

from camille.models import XMPPChannel, XMPPMessage

# Register your models here.


@admin.action(description="Purge selected channels")
def purge_channel(modeladmin, request, queryset):
    XMPPMessage.objects.filter(channel__in=queryset).delete()


@admin.register(XMPPChannel)
class XMPPChannelAdmin(admin.ModelAdmin):
    list_display = ("jid", "prompt")
    actions = [purge_channel]


@admin.register(XMPPMessage)
class XMPPMessageAdmin(admin.ModelAdmin):
    list_display = ("channel", "sender", "timestamp", "role", "content")
