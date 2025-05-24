from django.contrib import admin
from django.utils.html import format_html
from .models import CommentReaction

@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing CommentReaction model.
    Provides a clear view of user reactions to comments with filtering and search capabilities.
    """
    # Display fields in the list view
    list_display = (
        'id',
        'user',
        'comment_preview',
        'reaction_type',
        'created_at'
    )

    # Fields to filter by in the sidebar
    list_filter = (
        'is_dislike',
        'created_at',
        ('user', admin.RelatedFieldListFilter),
    )

    # Fields to search by
    search_fields = (
        'user__email',
        'comment__content',
        'user__profile__name'
    )

    # Fields that cannot be edited
    readonly_fields = (
        'id',
        'created_at'
    )

    # Use raw ID fields for better performance with large datasets
    raw_id_fields = (
        'user',
        'comment'
    )

    # Optimize queries by selecting related fields
    list_select_related = (
        'user',
        'user__profile',
        'comment'
    )

    # Order by most recent first
    ordering = ('-created_at',)

    # Number of items per page
    list_per_page = 20

    def comment_preview(self, obj):
        """Returns a truncated preview of the comment content."""
        if not obj.comment:
            return '-'
        return obj.comment.content[:50] + '...' if len(obj.comment.content) > 50 else obj.comment.content
    comment_preview.short_description = 'Comment'
    comment_preview.admin_order_field = 'comment__content'

    def reaction_type(self, obj):
        """Returns a formatted display of the reaction type."""
        if obj.is_dislike:
            return format_html(
                '<span style="color: #ba2121; font-weight: bold;">Dislike</span>'
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">Like</span>'
        )
    reaction_type.short_description = 'Reaction Type'
    reaction_type.admin_order_field = 'is_dislike'

    def get_queryset(self, request):
        """Optimizes the queryset by selecting related fields."""
        return super().get_queryset(request).select_related(
            'user',
            'user__profile',
            'comment'
        )

    def has_delete_permission(self, request, obj=None):
        """Restricts deletion to superusers only."""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Restricts modification to superusers only."""
        return request.user.is_superuser
