from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom password reset token generator.
    """
    def _make_hash_value(self, user, timestamp):
        """
        This method is used to generate the hash value.
        It includes the user's ID and last login timestamp.
        """
        return str(user.pk) + str(timestamp) + str(user.last_login)

password_reset_token_generator = PasswordResetTokenGenerator()
