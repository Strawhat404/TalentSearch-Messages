from django.contrib import admin
from .models import Message, MessageThread
from userprofile.models import Profile

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'receiver_name', 'message_preview', 'is_read', 'created_at')
    list_filter = ('sender', 'receiver', 'is_read', 'created_at')
    search_fields = ('message', 'sender__name', 'receiver__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def sender_name(self, obj):
        return obj.sender.name if obj.sender else 'Unknown Profile'
    sender_name.short_description = 'Sender'

    def receiver_name(self, obj):
        return obj.receiver.name if obj.receiver else 'Unknown Profile'
    receiver_name.short_description = 'Receiver'

    def message_preview(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_preview.short_description = 'Message'

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'participant_count', 'last_message_preview', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'participants__name')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('participants',)

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'

    def last_message_preview(self, obj):
        last_message = obj.get_last_message()
        if last_message:
            return last_message.message[:50] + ('...' if len(last_message.message) > 50 else '')
        return 'No messages'
    last_message_preview.short_description = 'Last Message'