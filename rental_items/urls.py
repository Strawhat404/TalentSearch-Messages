from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RentalItemViewSet, RatingViewSet

router = DefaultRouter()
router.register(r'items', RentalItemViewSet, basename='rental-item')
router.register(r'ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('', include(router.urls)),
] 