from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework import status
from django.http import JsonResponse
import sys
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework import serializers

User = get_user_model()

class SessionExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check session expiration for authenticated users
        if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False) and hasattr(request, 'session'):
            last_login = request.session.get('last_login')
            if last_login:
                try:
                    if isinstance(last_login, str):
                        from datetime import datetime
                        last_login = datetime.fromisoformat(last_login)
                    
                    # Check if session has expired
                    if (timezone.now() - last_login) > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                        # Clear the session
                        if hasattr(request.session, 'flush'):
                            request.session.flush()
                        # For API requests, return a JSON response
                        if request.path.startswith('/api/'):
                            return JsonResponse({
                                'error': 'Session has expired. Please log in again.'
                            }, status=status.HTTP_401_UNAUTHORIZED)
                except (ValueError, TypeError) as e:
                    print(f'DEBUG: Invalid session timestamp: {e}', file=sys.stderr)
                    if hasattr(request.session, 'flush'):
                        request.session.flush()
                    if request.path.startswith('/api/'):
                        return JsonResponse({
                            'error': 'Invalid session. Please log in again.'
                        }, status=status.HTTP_401_UNAUTHORIZED)
        
        response = self.get_response(request)
        return response 

class TokenRefreshSerializer(serializers.Serializer):
    """
    Enhanced token refresh serializer with additional validation and user info.
    """
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        
        try:
            # Validate the refresh token
            refresh = RefreshToken(refresh_token)
            
            # Check if token is blacklisted
            if refresh.token_type != 'refresh':
                raise serializers.ValidationError('Invalid token type')
            
            # Get user from token
            user_id = refresh.payload.get('user_id')
            if not user_id:
                raise serializers.ValidationError('Invalid token payload')
            
            # Verify user exists and is active
            try:
                user = User.objects.get(id=user_id, is_active=True)
                attrs['user'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError('User not found or inactive')
            
            attrs['refresh'] = refresh
            return attrs
            
        except Exception as e:
            raise serializers.ValidationError('Invalid refresh token')

class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer for token response with user information.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    expires_in = serializers.IntegerField(help_text="Access token expiry time in seconds")
    refresh_expires_in = serializers.IntegerField(help_text="Refresh token expiry time in seconds")

def refresh_user_tokens(user, old_refresh_token=None):
    """
    Utility function to refresh user tokens.
    
    Args:
        user: The user object
        old_refresh_token: Optional old refresh token to blacklist
    
    Returns:
        dict: New access and refresh tokens with expiry information
    """
    # Blacklist old refresh token if provided
    if old_refresh_token:
        try:
            old_refresh = RefreshToken(old_refresh_token)
            old_refresh.blacklist()
        except Exception:
            pass  # Ignore errors for old token blacklisting
    
    # Generate new tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    # Calculate expiry times
    now = timezone.now()
    access_expiry = access.current_time + access.lifetime
    refresh_expiry = refresh.current_time + refresh.lifetime
    
    expires_in = int((access_expiry - now).total_seconds())
    refresh_expires_in = int((refresh_expiry - now).total_seconds())
    
    return {
        'access': str(access),
        'refresh': str(refresh),
        'expires_in': expires_in,
        'refresh_expires_in': refresh_expires_in,
    }

def is_token_expiring_soon(token_str, threshold_minutes=5):
    """
    Check if a token is expiring soon.
    
    Args:
        token_str: The token string
        threshold_minutes: Minutes before expiry to consider "soon"
    
    Returns:
        bool: True if token expires soon, False otherwise
    """
    try:
        token = AccessToken(token_str)
        now = timezone.now()
        expiry = token.current_time + token.lifetime
        
        return expiry - now < timedelta(minutes=threshold_minutes)
    except Exception:
        return False

class AutoTokenRefreshMiddleware:
    """
    Middleware to automatically refresh tokens when they're about to expire.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only process for authenticated requests
        if hasattr(request, 'user') and request.user.is_authenticated:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header.split(' ')[1]
                try:
                    token = AccessToken(token_str)
                    now = timezone.now()
                    expiry = token.current_time + token.lifetime
                    
                    # If token expires in less than 5 minutes, add a header to suggest refresh
                    if expiry - now < timedelta(minutes=5):
                        response['X-Token-Expires-Soon'] = 'true'
                        response['X-Token-Expires-At'] = expiry.isoformat()
                        
                except Exception:
                    pass
        
        return response 