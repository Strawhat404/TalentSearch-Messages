# talentsearch/middleware.py
from django_ratelimit.decorators import ratelimit
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class AdminRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            @ratelimit(key='ip', rate='10/m', method='ALL')
            def limited_view(request):
                return self.get_response(request)
            response = limited_view(request)
            if getattr(response, 'limited', False):
                return HttpResponseForbidden('Rate limit exceeded')
            return response
        return self.get_response(request)

class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt all API URLs from CSRF protection
    """
    def process_request(self, request):
        # Exempt all API URLs from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None