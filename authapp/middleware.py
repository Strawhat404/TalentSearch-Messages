from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework import status
from django.http import JsonResponse
import sys

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