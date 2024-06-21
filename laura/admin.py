from django.contrib import admin

from laura.models import XMPPChannel, XMPPMessage


@admin.register(XMPPChannel)
class XMPPChannelAdmin(admin.ModelAdmin):
    list_display = ("jid", "model", "prompt")


@admin.register(XMPPMessage)
class XMPPMessageAdmin(admin.ModelAdmin):
    list_display = ("channel", "timestamp", "sender", "role", "body")
