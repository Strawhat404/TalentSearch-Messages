# userprofile/urls.py
from django.urls import path
from .views import ProfileView, VerificationView, VerificationAuditLogView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/<int:profile_id>/verify/', VerificationView.as_view(), name='verify_profile'),
    path('profile/<int:profile_id>/verification-logs/', VerificationAuditLogView.as_view(), name='verification_logs'),
]