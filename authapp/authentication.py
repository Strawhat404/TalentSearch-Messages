from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework import exceptions
from django.utils import timezone
import sys
import jwt

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        print('DEBUG: CustomJWTAuthentication called', file=sys.stderr)
        header = self.get_header(request)
        if header is None:
            return None
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        try:
            # First decode the token to check expiration
            token = AccessToken(raw_token)
            current_time = timezone.now().timestamp()
            if token['exp'] < current_time:
                print('DEBUG: Token is expired', file=sys.stderr)
                raise exceptions.AuthenticationFailed(
                    'Your session has expired. Please log in again.',
                    code='token_expired'
                )
            
            # Then validate the token for other claims
            validated_token = self.get_validated_token(raw_token)
            
            # Check for blacklisting
            jti = validated_token['jti']
            if BlacklistedToken.objects.filter(token__jti=jti).exists():
                print('DEBUG: Token is blacklisted', file=sys.stderr)
                raise exceptions.AuthenticationFailed(
                    'This session has been invalidated. Please log in again.',
                    code='token_blacklisted'
                )
            
            # Get user and validate password change timestamp
            user = self.get_user(validated_token)
            if user is None or not user.is_active:
                print('DEBUG: User not found or inactive', file=sys.stderr)
                raise exceptions.AuthenticationFailed(
                    'User account is inactive or not found.',
                    code='user_not_found'
                )
            
            # Check if password was changed after token was issued
            token_pwd_time = validated_token.get('last_password_change')
            user_pwd_time = user.last_password_change.timestamp() if user.last_password_change else 0
            
            if token_pwd_time:
                # If token has last_password_change claim, use it
                if user_pwd_time > token_pwd_time:
                    print('DEBUG: Password was changed after token was issued', file=sys.stderr)
                    raise exceptions.AuthenticationFailed(
                        'Your password has been changed. Please log in again.',
                        code='password_changed'
                    )
            elif user.last_password_change:
                # If token doesn't have last_password_change but user has a password change timestamp,
                # only invalidate if password was changed significantly after token issuance (e.g., > 1 minute)
                token_iat = validated_token.get('iat')
                if token_iat and (user_pwd_time - token_iat) > 60:  # 60 seconds grace period
                    print('DEBUG: Password was changed significantly after token was issued', file=sys.stderr)
                    raise exceptions.AuthenticationFailed(
                        'Your password has been changed. Please log in again.',
                        code='password_changed'
                    )
            
            # Update last login time in session
            if hasattr(request, 'session'):
                request.session['last_login'] = timezone.now().isoformat()
                if hasattr(request.session, 'save'):
                    request.session.save()
            
            return (user, validated_token)
        except TokenError as e:
            print(f'DEBUG: TokenError: {e}', file=sys.stderr)
            raise exceptions.AuthenticationFailed(
                'Invalid authentication token. Please log in again.',
                code='token_not_valid'
            )
        except jwt.ExpiredSignatureError:
            print('DEBUG: Token has expired', file=sys.stderr)
            raise exceptions.AuthenticationFailed(
                'Your session has expired. Please log in again.',
                code='token_expired'
            )
        except Exception as e:
            print(f'DEBUG: Exception: {e}', file=sys.stderr)
            raise exceptions.AuthenticationFailed(
                'Authentication failed. Please log in again.',
                code='token_not_valid'
            )

    def authenticate_header(self, request):
        return 'Bearer' 