# feed/urls.py

from django.urls import path
from .views import (
    FeedPostListView, FeedPostDetailView, FeedPostMediaView,
    FollowUserView, UnfollowUserView, FollowersListView, FollowingListView,
    FeedLikeCreateView, FeedLikeDeleteView,
    CommentListCreateView, CommentReplyCreateView, CommentLikeCreateView,
)

urlpatterns = [
    path('posts/', FeedPostListView.as_view(), name='feedpost-list'),
    path('posts/<uuid:id>/', FeedPostDetailView.as_view(), name='feedpost-detail'),
    path('posts/<uuid:id>/media/', FeedPostMediaView.as_view(), name='feedpost-media'),
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),
    path('following/', FollowingListView.as_view(), name='following-list'),
]

urlpatterns += [
    path('posts/<uuid:post_id>/like/', FeedLikeCreateView.as_view(), name='feed-like'),
    path('likes/<int:id>/unlike/', FeedLikeDeleteView.as_view(), name='feed-unlike'),
    path('posts/<uuid:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:parent_id>/reply/', CommentReplyCreateView.as_view(), name='comment-reply'),
    path('comments/<int:comment_id>/like/', CommentLikeCreateView.as_view(), name='comment-like'),
]
