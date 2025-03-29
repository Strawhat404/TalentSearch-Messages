from django.urls import path
from .views import SendMessageView, FetchMessagesView

urlpatterns = [
    path('send/', SendMessageView.as_view(), name='send_message'),
    path('fetch/', FetchMessagesView.as_view(), name='fetch_messages'),
]