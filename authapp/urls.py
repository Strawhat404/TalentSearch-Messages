from django.urls import path
from .views import RegisterView, LoginView, AdminLoginView, ForgotPasswordView, ResetPasswordView, NotificationListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.authtoken.views import obtain_auth_token  

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # JWT token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),  # Auth token
]
