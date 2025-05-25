from django.urls import path
from .views import (
    RegisterView, LoginView, AdminLoginView, ForgotPasswordView,
    ResetPasswordView, NotificationListView, ChangePasswordView,
    LogoutView, CustomTokenObtainPairView, RotateAPIKeyView,
    LogoutAllDevicesView
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Core authentication endpoints
    path('register/', RegisterView.as_view(), name='v2_register'),
    path('login/', LoginView.as_view(), name='v2_login'),
    path('admin/login/', AdminLoginView.as_view(), name='v2_admin_login'),
    path('logout/', LogoutView.as_view(), name='v2_logout'),
    
    # Password management
    path('forgot-password/', ForgotPasswordView.as_view(), name='v2_forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='v2_reset_password'),
    path('password-change/', ChangePasswordView.as_view(), name='v2_change_password'),
    
    # Token management
    path('token/', CustomTokenObtainPairView.as_view(), name='v2_token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='v2_token_refresh'),
    path('token/rotate/', RotateAPIKeyView.as_view(), name='v2_rotate_api_key'),
    path('token/logout-all/', LogoutAllDevicesView.as_view(), name='v2_logout_all_devices'),
    
    # Other endpoints
    path('notifications/', NotificationListView.as_view(), name='v2_notifications'),
    path('api-token-auth/', obtain_auth_token, name='v2_api_token_auth'),
] 