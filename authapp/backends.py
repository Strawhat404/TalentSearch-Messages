from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import logging

UserModel = get_user_model()
logger = logging.getLogger(__name__)

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate with either username or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        if not username:
            return None

        user = None
        # Try username
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Try email
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user using email and password.
        """
        try:
            # Get email from kwargs or username parameter
            email = kwargs.get('email')
            if email is None:
                email = username
            
            logger.debug(f"Attempting authentication for email: {email}")
            
            # Validate inputs
            if not email or not isinstance(email, str) or not email.strip():
                logger.warning("Authentication failed: Empty or invalid email")
                return None
            
            if not password or not isinstance(password, str) or not password.strip():
                logger.warning("Authentication failed: Empty or invalid password")
                return None
            
            # Normalize email
            email = email.strip().lower()
            
            try:
                # Get user by email
                user = UserModel.objects.get(email__iexact=email)
                logger.debug(f"Found user for email {email}: {user.id}")
                
                # Check password and user status
                if user.check_password(password):
                    if self.user_can_authenticate(user):
                        logger.info(f"Authentication successful for user {user.id}")
                        return user
                    else:
                        logger.warning(f"User {user.id} cannot be authenticated (inactive or locked)")
                else:
                    logger.warning(f"Invalid password for user {user.id}")
                    
            except UserModel.DoesNotExist:
                logger.warning(f"No user found for email: {email}")
                return None
                
        except Exception as e:
            logger.exception(f"Authentication error: {str(e)}")
            return None
            
        return None
