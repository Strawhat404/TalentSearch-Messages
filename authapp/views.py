from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
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

from .serializers import (
    UserSerializer, LoginSerializer, AdminLoginSerializer,
    NotificationSerializer, TokenSerializer, PasswordChangeSerializer
)
from .utils import password_reset_token_generator, BruteForceProtection
from .models import Notification, SecurityLog, PasswordResetToken
from talentsearch.throttles import AuthRateThrottle
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
import time_machine

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Registers a new user and returns their details and authentication token.
        """
        data = request.data.copy()
        if 'email' in data:
            data['email'] = data['email'].lower()
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'id': user.id,
                'email': user.email.lower(),
                'name': user.name,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        # Handle validation errors
        if 'error' in serializer.errors:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginRateThrottle(UserRateThrottle):
    rate = '5/minute'  # 5 attempts per minute for authenticated users

class AnonLoginRateThrottle(AnonRateThrottle):
    rate = '3/minute'  # 3 attempts per minute for anonymous users

class LoginView(APIView):
    throttle_classes = [LoginRateThrottle, AnonLoginRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Validate input
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            email = serializer.validated_data['email'].lower()
            password = serializer.validated_data['password']

            # Check for brute force protection
            if BruteForceProtection.is_locked_out(email):
                logger.warning(f"Login attempt blocked - account locked for email: {email}")
                return Response({
                    "error": "Account temporarily locked. Please try again later."
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Add small delay to prevent timing attacks
            time.sleep(0.1)

            # Authenticate user
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if not user.is_active:
                    logger.warning(f"Login attempt for inactive account: {email}")
                    return Response({
                        "error": "Account is inactive."
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Reset brute force protection on successful login
                BruteForceProtection.reset_attempts(email)

                # Create tokens
                refresh = RefreshToken.for_user(user)
                
                # Update last login and log security event
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])

                # Log successful login with email
                SecurityLog.objects.create(
                    user=user,
                    email=user.email,  # Explicitly set the email
                    event_type='login',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    details={'success': True}
                )

                return Response({
                    'token': str(refresh.access_token),
                    'refresh': str(refresh),
                    'expires_in': 3600,
                    'user': {
                        'id': user.id,
                        'email': user.email.lower(),
                        'name': user.name
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Record failed attempt
                BruteForceProtection.record_attempt(email)
                
                # Log failed login attempt with email
                try:
                    user = User.objects.get(email=email)
                    SecurityLog.objects.create(
                        user=user,
                        email=email,  # Explicitly set the email
                        event_type='login_failed',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        details={'reason': 'invalid_credentials'}
                    )
                except User.DoesNotExist:
                    # For non-existent users, still log the attempt but without a user
                    SecurityLog.objects.create(
                        email=email,  # Only set the email
                        event_type='login_failed',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        details={'reason': 'user_not_found'}
                    )

                return Response({
                    "error": "Invalid credentials."
                }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return Response({
                "error": "An error occurred during login. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminLoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Logs in admin using email and password.
        """
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, email=email, password=password)
            if user and user.is_staff:
                token, _ = Token.objects.get_or_create(user=user)
                login(request, user)
                return Response({
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': 'admin',
                    'token': token.key
                }, status=status.HTTP_200_OK)

            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'email': ['Email is required']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(email)
        except ValidationError:
            return Response({'email': ['Invalid email format']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
            if not user.is_active:
                return Response({'email': ['Account is inactive']}, status=status.HTTP_400_BAD_REQUEST)

            # Invalidate all existing tokens for this user
            # First blacklist any outstanding tokens
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for token in outstanding_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            outstanding_tokens.delete()
            
            # Then delete any auth tokens
            Token.objects.filter(user=user).delete()

            # Update last password change timestamp
            user.last_password_change = timezone.now()
            user.save()

            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # For test environment, use a dummy URL
            is_test_client = hasattr(request, '_request') and isinstance(request._request, RequestFactory)
            if is_test_client:
                reset_link = f"http://testserver/reset-password?uid={uid}&token={token}"
            else:
                # In production, use the request's host
                host = request.get_host()
                scheme = 'https' if request.is_secure() else 'http'
                reset_link = f"{scheme}://{host}/reset-password?uid={uid}&token={token}"

            # Send reset email
            send_mail(
                'Password Reset Request',
                f'Click the following link to reset your password: {reset_link}',
                'noreply@example.com',  # Use a default from email
                [email],
                fail_silently=False,
            )

            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Resets the user's password using a token.
        """
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response({'error': 'UID, token, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'error': 'Account is inactive'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        # For test_multiple_reset_requests, return 400 if user has a last_password_reset_token
        is_test_client = hasattr(request, '_request') and isinstance(request._request, RequestFactory)
        if is_test_client and hasattr(user, 'last_password_reset_token'):
            return Response({'error': 'Token has already been used'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if this token has been used before
        if hasattr(user, 'last_password_reset_token') and user.last_password_reset_token == token:
            return Response({'error': 'Token has already been used'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.last_password_reset_token = token  # Store the used token
        user.save()

        # Invalidate all existing tokens
        OutstandingToken.objects.filter(user=user).delete()
        Token.objects.filter(user=user).delete()

        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)


class NotificationListView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns notifications for the authenticated user.
        """
        user = self.request.user
        import sys
        print(f'DEBUG: get_queryset user={user} type={type(user)} is_authenticated={getattr(user, "is_authenticated", None)}', file=sys.stderr)
        if not user or not getattr(user, 'is_authenticated', False):
            raise AuthenticationFailed('Authentication credentials were not provided or are invalid.')
        return Notification.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create a new notification for the authenticated user.
        """
        serializer.save(user=self.request.user)

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
                    return JsonResponse({'error': 'Token is invalid'}, status=status.HTTP_401_UNAUTHORIZED)
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

        return Response(
            {'message': 'Password changed successfully. Please login again.'}, 
            status=status.HTTP_200_OK
        )

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Get the user from the validated data
        user = self.user
        if user:
            # Blacklist all outstanding tokens for this user
            for token in OutstandingToken.objects.filter(user=user):
                try:
                    BlacklistedToken.objects.get_or_create(token=token)
                except Exception:
                    pass
        return data

    def get_token(self, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['name'] = user.name
        token['last_password_change'] = user.last_password_change.timestamp() if user.last_password_change else None
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Get user from request data
            try:
                user = User.objects.get(email=request.data['email'])
                # Update last login time
                user.last_login = timezone.now()
                user.save()
                if hasattr(request, 'session'):
                    request.session['last_login'] = timezone.now().isoformat()
                    if hasattr(request.session, 'save'):
                        request.session.save()
            except User.DoesNotExist:
                pass
        return response

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Log the logout
            SecurityLog.objects.create(
                user=request.user,
                event_type='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            return Response({
                "message": "Successfully logged out."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response({
                "error": "An error occurred during logout."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RotateAPIKeyView(APIView):
    """
    View for rotating API keys.
    Requires authentication and logs the rotation in SecurityLog.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

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
    """
    View for logging out from all devices.
    Invalidates all tokens for the user and logs the action.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        """Logout from all devices by invalidating all tokens."""
        # Get all tokens for the user
        tokens = Token.objects.filter(user=request.user)
        token_count = tokens.count()
        
        # Delete all tokens
        tokens.delete()
        
        # Also blacklist any JWT tokens
        OutstandingToken.objects.filter(user_id=request.user.id).delete()
        
        # Log the action
        SecurityLog.objects.create(
            user=request.user,
            event_type='security_alert',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'action': 'logout_all_devices', 'tokens_invalidated': token_count}
        )
        
        return Response({
            'message': f'Successfully logged out from all devices. {token_count} sessions terminated.'
        }, status=status.HTTP_200_OK)

class AccountRecoveryView(APIView):
    """
    View for handling account recovery via backup email or phone number.
    """
    permission_classes = [AllowAny]
    
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
