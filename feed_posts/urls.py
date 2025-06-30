from django.urls import path
from .views import FeedPostListView, FeedPostDetailView, FeedPostMediaView, FollowUserView, UnfollowUserView, FollowersListView, FollowingListView

app_name = 'feed_posts'

urlpatterns = [
    path('', FeedPostListView.as_view(), name='feed-post-list'),
    path('<uuid:id>/', FeedPostDetailView.as_view(), name='feed-post-detail'),
    path('<uuid:id>/delete-media/', FeedPostMediaView.as_view(), name='feed-post-delete-media'),
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),
    path('following/', FollowingListView.as_view(), name='following-list'),
]