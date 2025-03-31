from django.urls import path
from .views import NewsListView, NewsCreateView, NewsUpdateView, NewsDeleteView

urlpatterns = [
    path('', NewsListView.as_view(), name='news_list'),
    path('', NewsCreateView.as_view(), name='news_create'),  # Same path, different method
    path('<int:id>/', NewsUpdateView.as_view(), name='news_update'),
    path('<int:id>/', NewsDeleteView.as_view(), name='news_delete'),
]