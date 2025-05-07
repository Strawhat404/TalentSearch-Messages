# talentsearch/middleware.py
from django_ratelimit.decorators import ratelimit
from django.http import HttpResponseForbidden

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