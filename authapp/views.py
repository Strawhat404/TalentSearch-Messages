from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
import time
from django.test.client import RequestFactory
import logging
import uuid
from django.db import transaction, IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import AnonymousUser

from .serializers import (
    UserSerializer, LoginSerializer, AdminLoginSerializer,
    NotificationSerializer, TokenSerializer, PasswordChangeSerializer,
    ForgotPasswordOTPSerializer, ResetPasswordOTPSerializer, CustomTokenObtainPairSerializer,
    AdminUserSerializer, TokenRefreshSerializer, TokenResponseSerializer
)
from .utils import password_reset_token_generator, BruteForceProtection
from .models import Notification, SecurityLog, PasswordResetToken, PasswordResetOTP, UserReport
from talentsearch.throttles import AuthRateThrottle
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
import time_machine
import random
import re
from .services import notify_new_user_registration, notify_user_reported

User = get_user_model()
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'name', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='user@example.com'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, example='Test@1234'),
            },
        ),
        responses={
            201: openapi.Response(description="Success", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                'username': openapi.Schema(type=openapi.TYPE_STRING, example='JohnDoe'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example='1234567890'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='user@example.com'),
                'access': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...')
            })),
            400: openapi.Response(description="Error", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid input')
            }))
        }
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Notify admins about new user registration
        notify_new_user_registration(user)

        return Response({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'phone_number': user.phone_number,
            'email': user.email.lower(),
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)

class LoginRateThrottle(UserRateThrottle):
    rate = '1000/minute'  # or higher for testing

class AnonLoginRateThrottle(AnonRateThrottle):
    rate = '100/minute'  # 3 attempts per minute for anonymous users

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle, AnonLoginRateThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Get user from the response
            user = User.objects.get(email=request.data.get('email'))

            # Send login notification
            from .services import notify_user_login
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            notify_user_login(user, ip_address, user_agent)

        return response

class AdminLoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='admin@example.com'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, example='Admin@1234'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='admin@example.com'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, example='Admin User'),
                        'role': openapi.Schema(type=openapi.TYPE_STRING, example='admin'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...')
                    }
                )
            ),
            400: openapi.Response(
                description="Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid credentials')
                    }
                )
            ),
            401: openapi.Response(
                description="Not Admin",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='User is not an admin')
                    }
                )
            )
        }
    )

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user and user.is_staff:
                refresh = RefreshToken.for_user(user)
                login(request, user)
                return Response({
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': 'admin',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    example='test@example.com',
                    description='The email address associated with the user account. Must be a valid, registered email.'
                ),
            },
            description='Provide the email address to receive a 6-digit OTP for password reset.'
        ),
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='OTP sent to your email.')
                    },
                    example={
                        'message': 'OTP sent to your email.'
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request or email not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Email not found.')
                    },
                    example={
                        'error': 'Email not found.'
                    }
                )
            )
        }
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

        # Generate 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"

        # Save OTP to DB
        PasswordResetOTP.objects.create(user=user, otp=otp)

        # Send OTP via email
        send_mail(
            "Your Password Reset Code",
            f"Your OTP code is: {otp}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp', 'new_password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example='test@example.com'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, example='123456'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, example='NewPassword123!'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Password reset successful.')
                    }
                )
            ),
            400: openapi.Response(
                description="Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid OTP or expired.')
                    }
                )
            )
        }
    )
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Password strength check
        if not is_strong_password(new_password):
            return Response({
                "error": "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Find unused, recent OTP
        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=otp, is_used=False
        ).order_by('-created_at').first()

        if not otp_obj:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Optionally: Check if OTP is expired (e.g., valid for 10 minutes)
        if (timezone.now() - otp_obj.created_at).total_seconds() > 600:
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

class NotificationListView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='List notifications',
        description='Get all notifications for the authenticated user',
        responses={
            200: NotificationSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        },
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Create notification',
        description='Create a new notification for the authenticated user',
        request_body=NotificationSerializer(),
        responses={
            201: NotificationSerializer(),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
        },
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if not user or not getattr(user, 'is_authenticated', False):
            raise AuthenticationFailed('Authentication credentials were not provided or are invalid.')
        return Notification.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the user when creating a notification, avoiding duplicates."""
        user = self.request.user
        title = serializer.validated_data.get('title')
        message = serializer.validated_data.get('message')
        link = serializer.validated_data.get('link')

        # Check for existing unread notification with the same title, message, and link
        if Notification.objects.filter(
                user=user,
                title=title,
                message=message,
                link=link,
                read=False
        ).exists():
            return  # Skip creation if duplicate exists
        serializer.save(user=user)


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating, and deleting individual notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter notifications to only show user's own notifications."""
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Get a notification',
        description='Get a specific notification by ID.',
        responses={200: NotificationSerializer(), 401: 'Unauthorized', 404: 'Not found'},
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Update a notification',
        description='Update a specific notification by ID.',
        responses={200: NotificationSerializer(), 401: 'Unauthorized', 404: 'Not found'},
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Partially update a notification',
        description='Partially update a specific notification by ID.',
        responses={200: NotificationSerializer(), 401: 'Unauthorized', 404: 'Not found'},
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Delete a notification',
        description='Delete a specific notification by ID.',
        responses={204: 'No Content', 401: 'Unauthorized', 404: 'Not found'},
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        """
        Update notification and mark as read if requested.
        """
        notification = serializer.save()
        if serializer.validated_data.get('read', False):
            from .services import NotificationService
            NotificationService._update_unread_count(self.request.user)


class NotificationUnreadCountView(APIView):
    """
    View for getting unread notification count.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Get unread notification count',
        description='Get the number of unread notifications for the authenticated user',
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'unread_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=3)
                    }
                )
            ),
        },
    )
    def get(self, request):
        from .services import NotificationService
        unread_count = NotificationService.get_unread_count(request.user)

        return Response({
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)


class SystemNotificationView(APIView):
    """
    View for creating system notifications (admin only).
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Create system notification',
        description='Create a system notification for all users or specific users (admin only)',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, example='System Maintenance'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example='System will be down for maintenance'),
                'link': openapi.Schema(type=openapi.TYPE_STRING, example='https://example.com/maintenance'),
                'user_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    example=[1, 2, 3],
                    description='Optional: specific user IDs to notify. If not provided, all active users will be notified.'
                ),
            },
            required=['title', 'message']
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='System notification created'),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=150)
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            403: openapi.Response(description="Forbidden - Admin access required"),
        },
    )
    def post(self, request):
        title = request.data.get('title')
        message = request.data.get('message')
        link = request.data.get('link')
        user_ids = request.data.get('user_ids')

        if not title or not message:
            return Response(
                {'error': 'title and message are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .services import NotificationService

        if user_ids:
            # Notify specific users, avoiding duplicates
            user_ids = list(set(user_ids))  # Remove duplicate user_ids
            users = User.objects.filter(id__in=user_ids, is_active=True)
            notifications = []
            for user in users:
                # Check for existing unread notification
                if not Notification.objects.filter(
                        user=user,
                        title=title,
                        message=message,
                        link=link,
                        read=False
                ).exists():
                    try:
                        notification = NotificationService.create_notification(
                            user=user,
                            title=title,
                            message=message,
                            notification_type=NotificationService.NOTIFICATION_TYPES['SYSTEM'],
                            link=link
                        )
                        notifications.append(notification)
                    except Exception as e:
                        continue
        else:
            # Notify all active users, avoiding duplicates
            notifications = NotificationService.create_system_notification(
                title=title,
                message=message,
                link=link
            )

        return Response({
            'message': 'System notification created',
            'count': len(notifications)
        }, status=status.HTTP_200_OK)


class NotificationStatsView(APIView):
    """
    View for getting notification statistics.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Get notification statistics',
        description='Get notification statistics for the authenticated user',
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=25),
                        'unread_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                        'read_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=22),
                        'by_type': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            example={
                                'info': 10,
                                'warning': 5,
                                'alert': 2,
                                'system': 8
                            }
                        )
                    }
                )
            ),
        },
    )
    def get(self, request):
        user = request.user

        # Get counts
        total_count = Notification.objects.filter(user=user).count()
        unread_count = Notification.objects.filter(user=user, read=False).count()
        read_count = total_count - unread_count

        # Get counts by type
        by_type = {}
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            count = Notification.objects.filter(user=user, notification_type=notification_type).count()
            if count > 0:
                by_type[notification_type] = count

        return Response({
            'total_count': total_count,
            'unread_count': unread_count,
            'read_count': read_count,
            'by_type': by_type
        }, status=status.HTTP_200_OK)


class NotificationCleanupView(APIView):
    """
    View for cleaning up old notifications (admin only).
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Clean up old notifications',
        description='Clean up notifications older than specified days (admin only)',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'days': openapi.Schema(type=openapi.TYPE_INTEGER, example=30,
                                       description='Number of days to keep notifications'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Old notifications cleaned up'),
                        'deleted_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=150)
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            403: openapi.Response(description="Forbidden - Admin access required"),
        },
    )
    def post(self, request):
        days = request.data.get('days', 30)

        if not isinstance(days, int) or days < 1:
            return Response(
                {'error': 'days must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .services import NotificationService
        deleted_count = NotificationService.cleanup_old_notifications(days)

        return Response({
            'message': 'Old notifications cleaned up',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)

class TokenAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        from django.utils import timezone
        import jwt
        from django.conf import settings
        import sys

        # Handle JWT token authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            print('DEBUG: Bearer token detected', file=sys.stderr)
            token = auth_header.split(' ')[1]
            try:
                token_obj = AccessToken(token)
                jti = token_obj['jti']
                if BlacklistedToken.objects.filter(token__jti=jti).exists():
                    print('DEBUG: Token is blacklisted', file=sys.stderr)
                    return JsonResponse({'error': 'Token is invalid or blacklisted'}, status=status.HTTP_401_UNAUTHORIZED)
                try:
                    # Accessing 'exp' will raise if expired
                    _ = token_obj['exp']
                    user_id = token_obj.get('user_id')
                    try:
                        user = User.objects.get(id=user_id)
                        request.user = user
                        if not hasattr(request, 'session'):
                            request.session = {}
                        request.session['last_login'] = timezone.now().isoformat()
                        request.session.save()
                        print('DEBUG: Token valid, user authenticated', file=sys.stderr)
                    except User.DoesNotExist:
                        print('DEBUG: User not found for token', file=sys.stderr)
                        return JsonResponse({'error': 'User not found'}, status=status.HTTP_401_UNAUTHORIZED)
                except (TokenError, InvalidToken, jwt.ExpiredSignatureError, KeyError):
                    print('DEBUG: Token is expired', file=sys.stderr)
                    return JsonResponse({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                print(f'DEBUG: Exception in token auth: {e}', file=sys.stderr)
                return JsonResponse({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        # Handle session authentication
        elif hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
            print('DEBUG: Session authentication detected', file=sys.stderr)
            if not hasattr(request, 'session'):
                print('DEBUG: No session object', file=sys.stderr)
                return JsonResponse({'error': 'No active session'}, status=status.HTTP_401_UNAUTHORIZED)

            # For test client, session might be a dict
            if isinstance(request.session, dict):
                last_login = request.session.get('last_login')
            else:
                last_login = request.session.get('last_login')

            if last_login:
                try:
                    if isinstance(last_login, str):
                        last_login = datetime.fromisoformat(last_login)
                    session_age = (timezone.now() - last_login).total_seconds()
                    print(f'DEBUG: Session age: {session_age}', file=sys.stderr)
                    if session_age > settings.SESSION_COOKIE_AGE:
                        print('DEBUG: Session expired', file=sys.stderr)
                        if hasattr(request.session, 'flush'):
                            request.session.flush()
                        return JsonResponse({'error': 'Session has expired'}, status=status.HTTP_401_UNAUTHORIZED)
                except (ValueError, TypeError) as e:
                    print(f'DEBUG: Invalid session timestamp: {e}', file=sys.stderr)
                    if hasattr(request.session, 'flush'):
                        request.session.flush()
                    return JsonResponse({'error': 'Invalid session'}, status=status.HTTP_401_UNAUTHORIZED)

            # Update last login time
            if isinstance(request.session, dict):
                request.session['last_login'] = timezone.now().isoformat()
            else:
                request.session['last_login'] = timezone.now().isoformat()
                request.session.save()
            print('DEBUG: Session valid, user authenticated', file=sys.stderr)

        response = self.get_response(request)
        return response

class ChangePasswordView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, example='OldPassword123!'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, example='NewPassword123!'),
            },
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Password changed successfully. Please login again.')
                    }
                )
            ),
            400: openapi.Response(
                description="Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid old password')
                    }
                )
            )
        }
    )
    def post(self, request):
        """
        Changes the user's password and invalidates all existing tokens.
        """
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Verify old password
        if not request.user.check_password(old_password):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password using the model's set_password method
        # This will automatically update last_password_change
        request.user.set_password(new_password)
        request.user.save()

        # Blacklist all JWT tokens
        OutstandingToken.objects.filter(user=request.user).delete()

        # Clear session
        request.session.flush()

        # Send password change notification
        from .services import notify_password_change
        ip_address = request.META.get('REMOTE_ADDR')
        notify_password_change(request.user, ip_address)

        return Response(
            {'message': 'Password changed successfully. Please login again.'},
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist'),
                'access': openapi.Schema(type=openapi.TYPE_STRING, description='Access token to blacklist (optional)')
            }
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Successfully logged out')
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Refresh token is required')
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid token')
                    }
                )
            )
        }
    )
    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

        refresh_token = request.data.get('refresh')
        access_token = request.data.get('access')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Blacklist refresh token
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optionally blacklist access token if provided
        if access_token:
            try:
                access = AccessToken(access_token)
                jti = access['jti']
                outstanding = OutstandingToken.objects.filter(jti=jti).first()
                if outstanding:
                    BlacklistedToken.objects.get_or_create(token=outstanding)
            except Exception:
                pass  # Ignore access token errors, since refresh is the main one

        # Clear session if exists
        if hasattr(request, 'session'):
            request.session.flush()

            # Log the logout
            SecurityLog.objects.create(
                user=request.user,
                event_type='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

class RotateAPIKeyView(APIView):
    """
    View for rotating API keys.
    Requires authentication and logs the rotation in SecurityLog.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    @swagger_auto_schema(
        tags=['auth'],
        summary='Rotate API key',
        description='Generate a new API key and invalidate the old one',
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'api_key': openapi.Schema(type=openapi.TYPE_STRING, example='new-api-key-token'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='API key rotated successfully')
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized"),
        },
    )
    def post(self, request):
        """Rotate the user's API key."""
        # Delete existing token
        Token.objects.filter(user=request.user).delete()

        # Create new token
        token = Token.objects.create(user=request.user)

        # Log the rotation
        SecurityLog.objects.create(
            user=request.user,
            event_type='api_key_rotation',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'old_token_id': None, 'new_token_id': token.id}
        )

        return Response({
            'api_key': token.key,
            'message': 'API key rotated successfully'
        }, status=status.HTTP_200_OK)

class LogoutAllDevicesView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Successfully logged out from all devices')
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid token')
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            # Check if user is authenticated and not AnonymousUser
            if not request.user.is_authenticated or isinstance(request.user, AnonymousUser):
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Blacklist all outstanding tokens for this user
            tokens = OutstandingToken.objects.filter(user_id=request.user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            # Log the logout all devices
            SecurityLog.objects.create(
                user=request.user,
                event_type='logout_all_devices',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            return Response(
                {'message': 'Successfully logged out from all devices'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AccountRecoveryView(APIView):
    """
    View for handling account recovery via backup email or phone number.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['auth'],
        summary='Request account recovery',
        description='Request account recovery via backup email or phone number',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'identifier': {'type': 'string'},
                    'recovery_method': {'type': 'string', 'enum': ['email', 'phone']}
                },
                'required': ['identifier', 'recovery_method']
            }
        },
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Recovery instructions sent to your email')
                    }
                )
            ),
            404: openapi.Response(
                description="Account Not Found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='No account found with the provided information')
                    }
                )
            ),
            500: openapi.Response(
                description="Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='An error occurred during account recovery')
                    }
                )
            ),
        },
    )
    def post(self, request):
        identifier = request.data.get('identifier')  # email or phone
        recovery_method = request.data.get('recovery_method')  # 'email' or 'phone'

        try:
            if recovery_method == 'email':
                user = User.objects.get(backup_email=identifier)
            else:  # phone
                user = User.objects.get(phone_number=identifier)

            # Generate recovery token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Log recovery attempt
            SecurityLog.objects.create(
                user=user,
                action='account_recovery_requested',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details=f'Recovery requested via {recovery_method}'
            )

            # Send recovery email/SMS
            if recovery_method == 'email':
                send_recovery_email(user, token, uid)
            else:
                send_recovery_sms(user, token, uid)

            return Response({
                'message': f'Recovery instructions sent to your {recovery_method}'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'error': 'No account found with the provided information'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'An error occurred during account recovery'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(APIView):
    """
    View for retrieving and updating user profile information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve user profile information."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Update user profile information."""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def send_recovery_email(user, token, uid):
    """Send account recovery email to user."""
    subject = 'Account Recovery Request'
    message = f'''
    Hello {user.email},

    You have requested to recover your account. Please click the link below to reset your password:

    {settings.FRONTEND_URL}/recover-account/{uid}/{token}/

    If you did not request this, please ignore this email.

    Best regards,
    Your App Team
    '''
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_recovery_sms(user, token, uid):
    """Send account recovery SMS to user."""
    # Implement SMS sending logic here
    # This is a placeholder - you'll need to integrate with an SMS service
    pass

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]  # Prevent abuse

    def post(self, request):
        try:
            email = request.data.get('email', '').lower()
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    return Response({
                        "error": "Account is inactive."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Invalidate any existing reset tokens
                PasswordResetToken.objects.filter(
                    user=user,
                    used=False,
                    expires_at__gt=timezone.now()
                ).update(used=True)

                # Create new reset token
                token = PasswordResetToken.objects.create(
                    user=user,
                    expires_at=timezone.now() + timedelta(hours=24),
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )

                # Log the reset request
                SecurityLog.objects.create(
                    user=user,
                    event_type='password_reset_requested',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )

                # Send reset email (implement your email sending logic)
                # send_password_reset_email(user.email, token.token)

                return Response({
                    "message": "If an account exists with this email, you will receive password reset instructions."
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                # Don't reveal if email exists or not
                return Response({
                    "message": "If an account exists with this email, you will receive password reset instructions."
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}", exc_info=True)
            return Response({
                "error": "An error occurred. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        tags=['auth'],
        summary='Confirm password reset',
        description='Reset password using a valid reset token',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string'},
                    'password': {'type': 'string', 'format': 'password'}
                },
                'required': ['token', 'password']
            }
        },
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Password has been reset successfully.')
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid Token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid or expired token.')
                    }
                )
            ),
            500: openapi.Response(
                description="Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='An error occurred. Please try again.')
                    }
                )
            )
        },
    )
    def post(self, request):
        try:
            token = request.data.get('token')
            new_password = request.data.get('password')

            if not token or not new_password:
                return Response({
                    "error": "Token and new password are required."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                reset_token = PasswordResetToken.objects.get(
                    token=token,
                    used=False,
                    expires_at__gt=timezone.now()
                )

                # Check if new password is same as old
                if reset_token.user.check_password(new_password):
                    return Response({
                        "error": "New password must be different from the current password."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Update password
                reset_token.user.set_password(new_password)
                reset_token.user.save()

                # Mark token as used
                reset_token.invalidate()

                # Log the password change
                SecurityLog.objects.create(
                    user=reset_token.user,
                    event_type='password_changed',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )

                return Response({
                    "message": "Password has been reset successfully."
                }, status=status.HTTP_200_OK)

            except PasswordResetToken.DoesNotExist:
                return Response({
                    "error": "Invalid or expired token."
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Password reset confirmation error: {str(e)}", exc_info=True)
            return Response({
                "error": "An error occurred. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def is_strong_password(password):
    # At least 8 characters, one uppercase, one lowercase, one digit, one special char
    if (len(password) < 8 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[^\w\s]', password)):
        return False
    return True

class AdminUserListView(generics.ListAPIView):
    """
    API view for admins to list all users.
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

class UserRegistrationView(APIView):
    pass

class NotificationMarkAllAsReadView(APIView):
    """
    Mark all notifications as read for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Mark all notifications as read',
        description='Mark all notifications as read for the authenticated user.',
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='All notifications marked as read'),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=5)
                    }
                )
            ),
        },
    )
    def post(self, request):
        from .services import NotificationService
        count = NotificationService.mark_all_as_read(request.user)
        return Response({
            'message': 'All notifications marked as read',
            'count': count
        }, status=status.HTTP_200_OK)

class NotificationMarkReadView(APIView):
    """
    View for marking a notification as read.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['notifications'],
        summary='Mark notification as read',
        description='Mark a specific notification as read for the authenticated user.',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'notification_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, description='ID of the notification to mark as read'),
            },
            required=['notification_id']
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Notification marked as read'),
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            404: openapi.Response(description="Notification not found"),
        },
    )
    def post(self, request):
        notification_id = request.data.get('notification_id')

        if not notification_id:
            return Response(
                {'error': 'notification_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .services import NotificationService
        success = NotificationService.mark_as_read(notification_id, request.user)

        if success:
            return Response({
                'message': 'Notification marked as read',
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Notification not found or could not be marked as read'},
                status=status.HTTP_404_NOT_FOUND
            )

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Check for success login limit
        if BruteForceProtection.is_success_limited(email):
            return Response(
                {"detail": "Too many successful logins. Please wait before trying again."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # 1. Check if user is locked out
        if BruteForceProtection.is_locked_out(email):
            return Response(
                {
                    "detail": "Too many failed login attempts. Please try again later.",
                    "lockout_time": BruteForceProtection.get_lockout_time(email)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        user = authenticate(request, email=email, password=password)
        if user is not None:
            BruteForceProtection.reset_attempts(email)
            BruteForceProtection.record_successful_login(email)
            # ... (return token, etc.)
            return Response({"detail": "Login successful!"})
        else:
            BruteForceProtection.record_attempt(email)
            return Response(
                {
                    "detail": "Invalid credentials.",
                    "remaining_attempts": BruteForceProtection.get_remaining_attempts(email)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

class UserReportView(APIView):
    """
    View for reporting users.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        tags=['reports'],
        summary='Report a user',
        description='Report a user for inappropriate behavior or content',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['reported_user_id', 'reason'],
            properties={
                'reported_user_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=123, description='ID of the user being reported'),
                'reason': openapi.Schema(type=openapi.TYPE_STRING, enum=['inappropriate_content', 'spam', 'harassment', 'fake_profile', 'scam', 'other'], example='inappropriate_content', description='Reason for the report'),
                'details': openapi.Schema(type=openapi.TYPE_STRING, example='Additional details about the report', description='Optional additional details'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='User reported successfully'),
                        'report_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1)
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            404: openapi.Response(description="User not found"),
        },
    )
    def post(self, request):
        reported_user_id = request.data.get('reported_user_id')
        reason = request.data.get('reason')
        details = request.data.get('details', '')

        if not reported_user_id or not reason:
            return Response({
                'error': 'reported_user_id and reason are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            reported_user = User.objects.get(id=reported_user_id, is_active=True)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Prevent users from reporting themselves
        if reported_user.id == request.user.id:
            return Response({
                'error': 'You cannot report yourself'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has already reported this user for the same reason
        if UserReport.objects.filter(
            reporter=request.user,
            reported_user=reported_user,
            reason=reason
        ).exists():
            return Response({
                'error': 'You have already reported this user for this reason'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the report
        report = UserReport.objects.create(
            reporter=request.user,
            reported_user=reported_user,
            reason=reason,
            details=details
        )

        # Send notification to admins
        notify_user_reported(reported_user, request.user, reason)

        # Log the report for audit purposes
        SecurityLog.objects.create(
            user=request.user,
            email=request.user.email,
            event_type='user_reported',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'report_id': report.id,
                'reported_user_id': reported_user.id,
                'reported_user_email': reported_user.email,
                'reason': reason,
                'details': details
            }
        )

        return Response({
            'message': 'User reported successfully',
            'report_id': report.id
        }, status=status.HTTP_200_OK)

class EnhancedTokenRefreshView(APIView):
    """
    Enhanced token refresh view that provides better user experience.
    """
    permission_classes = [AllowAny]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        tags=['auth'],
        summary='Refresh access token',
        description='Refresh the access token using a valid refresh token',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Valid refresh token',
                    example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'username': openapi.Schema(type=openapi.TYPE_STRING, example='john_doe'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, example='john@example.com'),
                            }
                        ),
                        'expires_in': openapi.Schema(type=openapi.TYPE_INTEGER, example=3600),
                        'refresh_expires_in': openapi.Schema(type=openapi.TYPE_INTEGER, example=2592000),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Invalid refresh token')
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='Token expired or invalid')
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh = serializer.validated_data['refresh']
                user = serializer.validated_data['user']

                # Generate new tokens
                new_refresh = RefreshToken.for_user(user)
                new_access = new_refresh.access_token

                # Blacklist the old refresh token
                refresh.blacklist()

                # Calculate expiry times
                from django.utils import timezone
                now = timezone.now()
                access_expiry = new_access.current_time + new_access.lifetime
                refresh_expiry = new_refresh.current_time + new_refresh.lifetime

                expires_in = int((access_expiry - now).total_seconds())
                refresh_expires_in = int((refresh_expiry - now).total_seconds())

                return Response({
                    'access': str(new_access),
                    'refresh': str(new_refresh),
                    'user': UserSerializer(user).data,
                    'expires_in': expires_in,
                    'refresh_expires_in': refresh_expires_in,
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Token refresh error: {str(e)}")
                return Response({
                    'error': 'Failed to refresh token'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenStatusView(APIView):
    """
    View to check token status and get user information.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['auth'],
        summary='Check token status',
        description='Check if the current access token is valid and get user information',
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'username': openapi.Schema(type=openapi.TYPE_STRING, example='john_doe'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, example='john@example.com'),
                            }
                        ),
                        'expires_in': openapi.Schema(type=openapi.TYPE_INTEGER, example=3600),
                    }
                )
            ),
            401: openapi.Response(description="Token invalid or expired"),
        }
    )
    def get(self, request):
        # Token is already validated by IsAuthenticated permission
        user = request.user

        # Calculate remaining time for the token
        from rest_framework_simplejwt.tokens import AccessToken
        from django.utils import timezone

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token_str = auth_header.split(' ')[1]
            try:
                token = AccessToken(token_str)
                now = timezone.now()
                expiry = token.current_time + token.lifetime
                expires_in = max(0, int((expiry - now).total_seconds()))

                return Response({
                    'valid': True,
                    'user': UserSerializer(user).data,
                    'expires_in': expires_in,
                }, status=status.HTTP_200_OK)
            except Exception:
                pass

        return Response({
            'valid': False,
            'error': 'Invalid token'
        }, status=status.HTTP_401_UNAUTHORIZED)


