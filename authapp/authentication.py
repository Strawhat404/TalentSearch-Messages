from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError

class BlacklistCheckingJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)
        jti = validated_token.get('jti')
        if jti:
            try:
                outstanding_token = OutstandingToken.objects.get(jti=jti)
                if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                    raise AuthenticationFailed('Token is blacklisted')
            except OutstandingToken.DoesNotExist:
                pass  # If not found, treat as normal (could be access token not in DB)
        return validated_token
