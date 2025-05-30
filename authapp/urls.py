from django.urls import path
from .views import (
    RegisterView, LoginView, AdminLoginView, ForgotPasswordView, ResetPasswordView,
    NotificationListView, ChangePasswordView, LogoutView, LogoutAllDevicesView, AccountRecoveryView, UserProfileView,
    PasswordResetRequestView, PasswordResetConfirmView
)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Core Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout-all-devices/', LogoutAllDevicesView.as_view(), name='logout-all-devices'),
    
    # Password Management
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Account Management
    path('account-recovery/', AccountRecoveryView.as_view(), name='account-recovery'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    
    # Token Management (DRF Token only)
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
]
