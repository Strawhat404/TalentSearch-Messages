from django.urls import path
from .views import NewsView, NewsDetailView, NewsImageDetailView

urlpatterns = [
    path('', NewsView.as_view(), name='news_list_create'),
 
    path('<int:id>/', NewsDetailView.as_view(), name='news_detail'),
    path('news-images/<int:id>/', NewsImageDetailView.as_view(), name='newsimage-detail'),
]