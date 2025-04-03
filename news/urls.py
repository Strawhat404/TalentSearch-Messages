from django.urls import path
from .views import NewsView, NewsDetailView

urlpatterns = [
    path('', NewsView.as_view(), name='news_list_create'),
 
    path('<int:id>/', NewsDetailView.as_view(), name='news_detail'),
]