from django.urls import path
from .views import (
    RegisterView, AdminLoginView, ForgotPasswordView, ResetPasswordView,
    NotificationListView, ChangePasswordView, LogoutView, LogoutAllDevicesView, AccountRecoveryView, UserProfileView,
    PasswordResetRequestView, PasswordResetConfirmView, CustomTokenObtainPairView, AdminUserListView
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Core Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
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
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
]
