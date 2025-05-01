# talentsearch/throttles.py
from rest_framework.throttling import UserRateThrottle

class AuthRateThrottle(UserRateThrottle):
    scope = 'auth'

class CreateRateThrottle(UserRateThrottle):
    scope = 'create'