from django.urls import path
from .views import NewsView, NewsUpdateView, NewsDeleteView

urlpatterns = [
    path('', NewsView.as_view(), name='news_list_create'),
 
    path('<int:id>/', NewsUpdateView.as_view(), name='news_update'),
    path('<int:id>/', NewsDeleteView.as_view(), name='news_delete'),
]