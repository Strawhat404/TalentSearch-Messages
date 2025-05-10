from django.urls import path
from .views import GalleryItemListCreateView, GalleryItemDetailView

urlpatterns = [
    path('', GalleryItemListCreateView.as_view(), name='gallery-item-list-create'),
    path('<int:id>/', GalleryItemDetailView.as_view(), name='gallery-item-detail'),
]