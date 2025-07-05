from django.contrib import admin
from .models import FeedPost

@admin.register(FeedPost)
class FeedPostAdmin(admin.ModelAdmin):
    list_display = ('project_title', 'profile', 'project_type', 'location', 'media_type', 'created_at')
    list_filter = ('project_type', 'media_type', 'created_at')
    search_fields = ('project_title', 'content', 'location', 'profile__user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'profile', 'project_title', 'content')
        }),
        ('Media', {
            'fields': ('media_type', 'media_url')
        }),
        ('Project Details', {
            'fields': ('project_type', 'location')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 