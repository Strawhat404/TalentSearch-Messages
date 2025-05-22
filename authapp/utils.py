from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom password reset token generator.
    """
    def _make_hash_value(self, user, timestamp):
        """
        This method is used to generate the hash value.
        It includes only essential fields:
        - User's ID
        - Timestamp
        - Password hash (changes when password changes)
        """
        return (
            six.text_type(user.pk) + 
            six.text_type(timestamp) + 
            six.text_type(user.password)
        )

password_reset_token_generator = PasswordResetTokenGenerator()
