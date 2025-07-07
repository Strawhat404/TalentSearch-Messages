from django.contrib import admin
from .models import FeedPost, FeedLike, Follow, Comment, CommentLike

@admin.register(FeedPost)
class FeedPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'project_title', 'media_type', 'created_at')
    search_fields = ('project_title', 'content', 'profile__user__email')
    list_filter = ('media_type', 'project_type', 'created_at')

@admin.register(FeedLike)
class FeedLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'profile', 'created_at')
    search_fields = ('post__project_title', 'profile__user__email')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__user__email', 'following__user__email')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'profile', 'content', 'parent', 'created_at')
    search_fields = ('content', 'profile__user__email', 'post__project_title')
    list_filter = ('created_at',)

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'profile', 'created_at')
    search_fields = ('comment__content', 'profile__user__email')
