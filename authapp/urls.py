from django.urls import path, include
from .views import (
    RegisterView, LoginView, AdminLoginView, ForgotPasswordView, ResetPasswordView,
    NotificationListView, ChangePasswordView, LogoutView, CustomTokenObtainPairView,
    RotateAPIKeyView, LogoutAllDevicesView, AccountRecoveryView, UserProfileView
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Core Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    
    # Password Management
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('password-reset-request/', ForgotPasswordView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', ResetPasswordView.as_view(), name='password-reset-confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Account Management
    path('account-recovery/', AccountRecoveryView.as_view(), name='account-recovery'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout-all-devices/', LogoutAllDevicesView.as_view(), name='logout-all-devices'),
    
    # Token Management
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('rotate-api-key/', RotateAPIKeyView.as_view(), name='rotate-api-key'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    
    # API Versioning
    path('v1/auth/', include('authapp.urls_v1')),
    path('v2/auth/', include('authapp.urls_v2')),
]
