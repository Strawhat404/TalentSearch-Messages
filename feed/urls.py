# feed/urls.py

from django.urls import path
from .views import (
    FeedPostListView, FeedPostDetailView, FeedPostMediaView,
    FollowUserView, UnfollowUserView, FollowersListView, FollowingListView
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
