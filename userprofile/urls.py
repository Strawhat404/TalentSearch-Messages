# userprofile/urls.py
from django.urls import path
from .views import ProfileView, VerificationView, VerificationAuditLogView, ChoiceDataView

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),  # This will handle /api/profile/
    path('<int:profile_id>/verify/', VerificationView.as_view(), name='verify_profile'),
    path('<int:profile_id>/verification-logs/', VerificationAuditLogView.as_view(), name='verification_logs'),
    path('choices/', ChoiceDataView.as_view(), name='choice_data'),
]