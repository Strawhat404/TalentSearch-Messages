from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RentalItemViewSet, RentalItemListCreateView, WishlistViewSet,FeaturedItemAuditLogView
from rental_ratings.views import RatingViewSet

router = DefaultRouter()
router.register(r'items', RentalItemViewSet, basename='rental-item')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
    path('rental/', RentalItemListCreateView.as_view(), name='rentalitem-list-create'),
    path('featured-logs/', FeaturedItemAuditLogView.as_view(), name='featured-item-audit-logs'),
] 