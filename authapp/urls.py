from django.urls import path
from .views import (
    RegisterView, AdminLoginView, ForgotPasswordView, ResetPasswordView,
    NotificationListView, NotificationDetailView, NotificationUnreadCountView,
    NotificationStatsView, SystemNotificationView, NotificationCleanupView,
    ChangePasswordView, LogoutView, LogoutAllDevicesView, AccountRecoveryView, UserProfileView,
    PasswordResetRequestView, PasswordResetConfirmView, CustomTokenObtainPairView, AdminUserListView,
    NotificationMarkAllAsReadView, NotificationMarkReadView
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
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    
    # Notification System
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('notifications/unread-count/', NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('notifications/stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('notifications/system/', SystemNotificationView.as_view(), name='system-notification'),
    path('notifications/cleanup/', NotificationCleanupView.as_view(), name='notification-cleanup'),
    path('notifications/mark-all-read/', NotificationMarkAllAsReadView.as_view(), name='notification-mark-all-read'),
]
