from django.contrib import admin
from .models import Comment, CommentLike

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'content_preview', 'parent', 'created_at', 'likes_count', 'dislikes_count')
    list_filter = ('created_at', 'parent')
    search_fields = ('content', 'user__email', 'post__id')
    readonly_fields = ('created_at', 'updated_at', 'likes_count', 'dislikes_count')
    raw_id_fields = ('user', 'post', 'parent')
    list_select_related = ('user', 'post', 'parent')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'user', 'is_like', 'created_at')
    list_filter = ('is_like', 'created_at')
    search_fields = ('comment__content', 'user__email')
    readonly_fields = ('created_at',)
    raw_id_fields = ('comment', 'user')
    list_select_related = ('comment', 'user')
