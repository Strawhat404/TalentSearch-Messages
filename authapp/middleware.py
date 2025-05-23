from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework import status
from django.http import JsonResponse

class SessionExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and 'last_login' in request.session:
            last_login = request.session['last_login']
            if isinstance(last_login, str):
                from datetime import datetime
                last_login = datetime.fromisoformat(last_login)
            
            # Check if session has expired
            if (timezone.now() - last_login) > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                # Clear the session
                request.session.flush()
                if request.path.startswith('/api/'):
                    return JsonResponse({'error': 'Session expired. Please login again.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        response = self.get_response(request)
        return response 