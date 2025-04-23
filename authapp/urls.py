from django.urls import path
from .views import RegisterView, LoginView, AdminLoginView, ForgotPasswordView,ResetPasswordView, NotificationListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),  # Ensure this line exists
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
]