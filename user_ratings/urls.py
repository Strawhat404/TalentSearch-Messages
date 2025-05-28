from django.urls import path
from .views import (
    UserRatingCreateListView,
    UserRatingSummaryView,
    UserRatingUpdateDeleteView
)

urlpatterns = [
    path('', UserRatingCreateListView.as_view(), name='user-rating-create'),
    path('', UserRatingCreateListView.as_view(), name='user-rating-list'),
    path('summary/', UserRatingSummaryView.as_view(), name='user-rating-summary'),
    path('<int:id>/', UserRatingUpdateDeleteView.as_view(), name='user-rating-update'),
    path('<int:id>/', UserRatingUpdateDeleteView.as_view(), name='user-rating-delete'),
]