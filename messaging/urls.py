from django.urls import path
from .views import MessageView, MessageThreadView, MessageThreadDetailView

urlpatterns = [
    # Thread endpoints
    path('threads/', MessageThreadView.as_view(), name='thread-list'),
    path('threads/<int:thread_id>/', MessageThreadDetailView.as_view(), name='thread-detail'),
    
    # Message endpoints
    path('messages/', MessageView.as_view(), name='message-list'),
]