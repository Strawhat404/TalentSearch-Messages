# adverts/urls.py
from django.urls import path
from .views import AdvertListCreateView, AdvertRetrieveUpdateDestroyView

urlpatterns = [
    path('', AdvertListCreateView.as_view(), name='advert-list-create'),
    path('<uuid:id>/', AdvertRetrieveUpdateDestroyView.as_view(), name='advert-retrieve-update-destroy'),
]