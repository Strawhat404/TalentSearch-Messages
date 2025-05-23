from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
import base64
import struct

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
