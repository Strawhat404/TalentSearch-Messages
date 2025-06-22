"""
Development settings for TalentSearch project.
"""

from .base import *
import os

DEBUG = True
SECRET_KEY = 'django-insecure-key-for-development-only'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email settings for development
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025
# EMAIL_HOST_USER = 'dev@example.com'
# EMAIL_HOST_PASSWORD = 'dev_password'
# EMAIL_USE_TLS = False
# DEFAULT_FROM_EMAIL = 'dev@example.com'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'abelyitages10@gmail.com'
EMAIL_HOST_PASSWORD = 'jmkj xtvh mnst zlex'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'abelyitages10@gmail.com'

# Redis settings for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Optional Redis support for dev
if env('REDIS_URL', default=None):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Fallback to simple in-memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# CORS settings for local frontend devs
CORS_ALLOWED_ORIGINS = [
    "https://talentdiscovery1.netlify.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_ALL_ORIGINS = True  # For dev only, allows all origins

# Override REST Framework settings for development to include missing throttle rates
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authapp.authentication.BlacklistCheckingJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'test': '1000/minute',
        'auth': '10/minute',
        'create': '10/minute',  # Add the missing 'create' scope
    },
}