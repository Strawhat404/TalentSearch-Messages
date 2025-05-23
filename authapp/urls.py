from django.urls import path
from .views import RegisterView, LoginView, AdminLoginView, ForgotPasswordView, ResetPasswordView, NotificationListView, ChangePasswordView, LogoutView, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.authtoken.views import obtain_auth_token  

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', ForgotPasswordView.as_view(), name='password_reset'),
    path('password-reset/confirm/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    path('password-change/', ChangePasswordView.as_view(), name='password_change'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),  # Auth token
]
