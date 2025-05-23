from django.urls import path
from .views import FeedLikeListView, FeedLikeDeleteView

app_name = 'feed_likes'

urlpatterns = [
    path('', FeedLikeListView.as_view(), name='feed-like-list'),
    path('unlike/', FeedLikeDeleteView.as_view(), name='feed-like-delete'),
]
