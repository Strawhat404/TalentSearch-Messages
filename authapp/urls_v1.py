from django.urls import path
from .views import (
    RegisterView, LoginView, AdminLoginView, ForgotPasswordView,
    ResetPasswordView, NotificationListView, ChangePasswordView,
    LogoutView, CustomTokenObtainPairView
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('register/', RegisterView.as_view(), name='v1_register'),
    path('login/', LoginView.as_view(), name='v1_login'),
    path('admin/login/', AdminLoginView.as_view(), name='v1_admin_login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='v1_forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='v1_reset_password'),
    path('notifications/', NotificationListView.as_view(), name='v1_notifications'),
    path('logout/', LogoutView.as_view(), name='v1_logout'),
    path('password-change/', ChangePasswordView.as_view(), name='v1_change_password'),
    path('token/', CustomTokenObtainPairView.as_view(), name='v1_token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='v1_token_refresh'),
    path('api-token-auth/', obtain_auth_token, name='v1_api_token_auth'),
] 