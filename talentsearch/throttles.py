# talentsearch/throttles.py
from rest_framework.throttling import UserRateThrottle, SimpleRateThrottle

class AuthRateThrottle(UserRateThrottle):
    scope = 'auth'

class CreateRateThrottle(UserRateThrottle):
    scope = 'create'

class PerThreadMessageThrottle(SimpleRateThrottle):
    """
    Limits the number of messages a user can send to a specific thread per minute.
    The scope is user+thread, so each user can send up to N messages per thread per minute.
    Set the rate via the 'rate' class attribute (e.g., '15/minute').
    """
    scope = 'per_thread_message'
    rate = '15/minute'  # Updated to 15 messages per thread per minute

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None  # Only throttle authenticated users
        thread_id = None
        # Try to get thread ID from request data (POST) or query params (GET)
        if request.method == 'POST':
            thread_id = request.data.get('thread') or request.data.get('thread_id')
        else:
            thread_id = request.query_params.get('thread') or request.query_params.get('thread_id')
        if not thread_id:
            return None  # No thread specified; do not throttle
        return f"throttle_{self.scope}_{request.user.pk}_{thread_id}"

class PerThreadViewThrottle(SimpleRateThrottle):
    """
    Limits the number of GET requests a user can make to a specific thread per minute.
    The scope is user+thread, so each user can view a thread up to N times per minute.
    Set the rate via the 'rate' class attribute (e.g., '30/minute').
    """
    scope = 'per_thread_view'
    rate = '30/minute'  # Example: 30 views per thread per minute

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None  # Only throttle authenticated users
        thread_id = None
        # Try to get thread ID from URL kwargs or query params
        thread_id = getattr(view, 'kwargs', {}).get('thread_id')
        if not thread_id:
            thread_id = request.query_params.get('thread') or request.query_params.get('thread_id')
        if not thread_id:
            return None  # No thread specified; do not throttle
        return f"throttle_{self.scope}_{request.user.pk}_{thread_id}"

class PerMessageViewThrottle(SimpleRateThrottle):
    """
    Limits the number of GET requests a user can make to a specific message per minute.
    The scope is user+message, so each user can view a message up to N times per minute.
    Set the rate via the 'rate' class attribute (e.g., '30/minute').
    """
    scope = 'per_message_view'
    rate = '30/minute'  # Example: 30 views per message per minute

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None  # Only throttle authenticated users
        message_id = None
        # Try to get message ID from URL kwargs or query params
        message_id = getattr(view, 'kwargs', {}).get('message_id')
        if not message_id:
            message_id = request.query_params.get('message') or request.query_params.get('message_id')
        if not message_id:
            return None  # No message specified; do not throttle
        return f"throttle_{self.scope}_{request.user.pk}_{message_id}"