from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'message_preview', 'is_read', 'created_at')
    list_filter = ('sender', 'receiver', 'is_read', 'created_at')
    search_fields = ('message',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def message_preview(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_preview.short_description = 'Message'