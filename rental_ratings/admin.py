from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'item_id', 'user', 'rating', 'is_verified_purchase', 
        'helpful_votes', 'reported', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified_purchase', 'reported', 'is_edited',
        'created_at', 'updated_at'
    ]
    search_fields = ['item_id', 'user__email', 'user__username', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'item_id', 'user', 'rating', 'comment')
        }),
        ('Status', {
            'fields': ('is_verified_purchase', 'reported', 'is_edited')
        }),
        ('Engagement', {
            'fields': ('helpful_votes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False  # Ratings should only be created through the API
