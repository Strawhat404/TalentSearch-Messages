from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
import base64
import struct
from django.core.cache import cache
import logging
from rest_framework import serializers
from .models import User
from .serializers import UserSerializer

logger = logging.getLogger(__name__)

class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom password reset token generator with expiration.
    """
    def _make_hash_value(self, user, timestamp):
        """
        Generate hash value for token.
        Includes:
        - User's ID
        - Timestamp
        - Password hash
        - Last login timestamp
        """
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return (
            six.text_type(user.pk) + 
            six.text_type(timestamp) + 
            six.text_type(user.password) +
            six.text_type(login_timestamp)
        )

    def check_token(self, user, token):
        # Only use Django's built-in expiration and validation
        return super().check_token(user, token)

def int_to_base36(i):
    """Convert an integer to a base36 string."""
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if i < 0:
        i = -i
    if i == 0:
        return "0"
    chars = []
    while i:
        i, remainder = divmod(i, 36)
        chars.append(digits[remainder])
    return "".join(reversed(chars))

def base36_to_int(s):
    """Convert a base36 string to an integer."""
    return int(s, 36)

password_reset_token_generator = PasswordResetTokenGenerator()

# Get password reset timeout from settings
PASSWORD_RESET_TIMEOUT = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 86400)  # 24 hours in seconds
PASSWORD_RESET_TOKEN_TIMEOUT = getattr(settings, 'PASSWORD_RESET_TOKEN_TIMEOUT', 86400)

class BruteForceProtection:
    """
    Implements brute force protection for login attempts.
    Uses cache to track failed attempts and implement lockouts.
    """
    # Number of failed attempts before lockout
    MAX_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
    # Lockout duration in seconds (default: 15 minutes)
    LOCKOUT_DURATION = getattr(settings, 'LOGIN_LOCKOUT_DURATION', 900)
    # Cache key prefix
    CACHE_KEY_PREFIX = 'login_attempts_'

    SUCCESSFUL_LOGIN_LIMIT = 7  # or whatever you want
    SUCCESSFUL_LOGIN_WINDOW = 60 * 5  # 5 minutes, for example

    @classmethod
    def _get_cache_key(cls, email):
        """Get cache key for the email"""
        return f"{cls.CACHE_KEY_PREFIX}{email.lower()}"

    @classmethod
    def _get_success_cache_key(cls, email):
        return f"success_logins_{email.lower()}"

    @classmethod
    def record_attempt(cls, email):
        """
        Record a failed login attempt for the given email.
        """
        cache_key = cls._get_cache_key(email)
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, cls.LOCKOUT_DURATION)
        
        logger.warning(
            f"Failed login attempt for {email}. "
            f"Attempt {attempts} of {cls.MAX_ATTEMPTS}"
        )

    @classmethod
    def reset_attempts(cls, email):
        """
        Reset failed attempts for the given email after successful login.
        """
        cache_key = cls._get_cache_key(email)
        cache.delete(cache_key)
        logger.info(f"Reset login attempts for {email}")

    @classmethod
    def is_locked_out(cls, email):
        """
        Check if the email is currently locked out.
        """
        cache_key = cls._get_cache_key(email)
        attempts = cache.get(cache_key, 0)
        return attempts >= cls.MAX_ATTEMPTS

    @classmethod
    def get_remaining_attempts(cls, email):
        """
        Get the number of remaining attempts before lockout.
        """
        cache_key = cls._get_cache_key(email)
        attempts = cache.get(cache_key, 0)
        return max(0, cls.MAX_ATTEMPTS - attempts)

    @classmethod
    def get_lockout_time(cls, email):
        """
        Get the remaining lockout time in seconds if locked out.
        Returns 0 if not locked out.
        """
        if not cls.is_locked_out(email):
            return 0
            
        cache_key = cls._get_cache_key(email)
        ttl = cache.ttl(cache_key)
        return max(0, ttl)

    @classmethod
    def record_successful_login(cls, email):
        cache_key = cls._get_success_cache_key(email)
        count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, count, cls.SUCCESSFUL_LOGIN_WINDOW)
        return count

    @classmethod
    def is_success_limited(cls, email):
        cache_key = cls._get_success_cache_key(email)
        count = cache.get(cache_key, 0)
        return count >= cls.SUCCESSFUL_LOGIN_LIMIT

class TokenRefreshSerializer(serializers.Serializer):
    """
    Enhanced token refresh serializer with additional validation and user info.
    """
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        
        try:
            # Validate the refresh token
            from rest_framework_simplejwt.tokens import RefreshToken
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
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.utils import timezone
    
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
        from rest_framework_simplejwt.tokens import AccessToken
        from django.utils import timezone
        from datetime import timedelta
        
        token = AccessToken(token_str)
        now = timezone.now()
        expiry = token.current_time + token.lifetime
        
        return expiry - now < timedelta(minutes=threshold_minutes)
    except Exception:
        return False
