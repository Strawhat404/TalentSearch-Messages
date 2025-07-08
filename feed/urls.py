# feed/urls.py

from django.urls import path
from .views import (
    FeedPostListView, FeedPostDetailView, FeedPostMediaView,
    FollowUserView, UnfollowUserView, FollowersListView, FollowingListView,
    FeedLikeToggleView,
    CommentListCreateView, CommentReplyCreateView, CommentLikeCreateView,
    CommentDeleteView,
)

urlpatterns = [
    path('posts/', FeedPostListView.as_view(), name='feedpost-list'),
    path('posts/<uuid:id>/', FeedPostDetailView.as_view(), name='feedpost-detail'),
    path('posts/<uuid:id>/media/', FeedPostMediaView.as_view(), name='feedpost-media'),
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),
    path('following/', FollowingListView.as_view(), name='following-list'),
    path('posts/<uuid:post_id>/like/', FeedLikeToggleView.as_view(), name='feed-like-toggle'),
    path('posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:parent_id>/reply/', CommentReplyCreateView.as_view(), name='comment-reply'),
    path('comments/<int:comment_id>/like/', CommentLikeCreateView.as_view(), name='comment-like'),
    path('comments/<int:id>/', CommentDeleteView.as_view(), name='comment-delete'),
]
