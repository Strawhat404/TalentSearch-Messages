from django.contrib import admin
from .models import FeedLike

@admin.register(FeedLike)
class FeedLikeAdmin(admin.ModelAdmin):
    list_display = ('profile', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('profile__user__username', 'post__project_title')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'profile', 'post')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
