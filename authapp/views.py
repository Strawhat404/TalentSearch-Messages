from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
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
from rest_framework_simplejwt.tokens import AccessToken
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.exceptions import AuthenticationFailed

from .serializers import (
    UserSerializer, LoginSerializer, AdminLoginSerializer,
    NotificationSerializer, TokenSerializer, PasswordChangeSerializer
)
from .utils import password_reset_token_generator
from .models import Notification
from talentsearch.throttles import AuthRateThrottle
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Registers a new user and returns their details and authentication token.
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        # Handle validation errors
        if 'error' in serializer.errors:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Logs the user in using email and password. Returns token on success.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

            if user.check_password(password):
                # Delete any existing tokens for this user
                Token.objects.filter(user=user).delete()
                
                # Create new token with expiration
                token = Token.objects.create(user=user)
                token.created = timezone.now()
                token.save()
                
                # Update last login
                user.last_login = timezone.now()
                user.save()
                
                return Response({
                    'token': token.key,
                    'expires_in': (settings.REST_FRAMEWORK.get('TOKEN_EXPIRE_MINUTES', 60)) * 60,  # Convert to seconds (fallback 60 minutes)
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': user.name
                    }
                }, status=status.HTTP_200_OK)

            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Sends a password reset link to the provided email.
        """
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return Response({'email': ['Invalid email format']}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        token = password_reset_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        frontend_url = getattr(settings, "FRONTEND_URL", "https://talentsearch-messages-uokp.onrender.com")
        reset_link = f"{frontend_url}/api/auth/reset-password/?uid={uid}&token={token}"

        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_link}',
            'noreply@example.com',
            [user.email],
            fail_silently=False,
        )
        return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)


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
            user = None

        if user is None or not password_reset_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
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
        """
        Logs out the user by blacklisting their token.
        """
        try:
            # Get the token from the Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                # Blacklist the token
                token_obj = OutstandingToken.objects.get(token=token)
                BlacklistedToken.objects.get_or_create(token=token_obj)
            
            # Clear session
            request.session.flush()
            
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except (OutstandingToken.DoesNotExist, IndexError):
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
