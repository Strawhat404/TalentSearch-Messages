from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
import base64
import struct
from django.core.cache import cache
import logging

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

    @classmethod
    def _get_cache_key(cls, email):
        """Get cache key for the email"""
        return f"{cls.CACHE_KEY_PREFIX}{email.lower()}"

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
        
        if attempts >= cls.MAX_ATTEMPTS:
            logger.warning(f"Login locked out for {email}")
            return True
            
        return False

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
