from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone

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
        """
        Check if token is valid and not expired.
        """
        if not super().check_token(user, token):
            return False
        
        # Check token expiration
        try:
            ts_b36, _ = token.split("-")
            ts = int(ts_b36, 36)
            token_time = timezone.datetime.fromtimestamp(ts, tz=dt_timezone.utc)
            if (timezone.now() - token_time) > timedelta(seconds=settings.PASSWORD_RESET_TOKEN_TIMEOUT):
                return False
        except (ValueError, TypeError):
            return False
        
        return True

password_reset_token_generator = PasswordResetTokenGenerator()

# Get password reset timeout from settings
PASSWORD_RESET_TIMEOUT = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 86400)  # 24 hours in seconds
PASSWORD_RESET_TOKEN_TIMEOUT = getattr(settings, 'PASSWORD_RESET_TOKEN_TIMEOUT', 86400)  # 24 hours in seconds
