from django.urls import path
from .views import FeedPostListView, FeedPostDetailView, FeedPostMediaView

app_name = 'feed_posts'

urlpatterns = [
    path('', FeedPostListView.as_view(), name='feed-post-list'),
    path('<uuid:id>/', FeedPostDetailView.as_view(), name='feed-post-detail'),
    path('<uuid:id>/delete-media/', FeedPostMediaView.as_view(), name='feed-post-delete-media'),
]