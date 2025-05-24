"""
Development settings for TalentSearch project.
"""

from .base import *
import dj_database_url
from decouple import config

DEBUG = config('DEBUG', cast=bool, default=True)

SECRET_KEY = config('SECRET_KEY', default='insecure-dev-key')

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]

# Use PostgreSQL or any DB via DATABASE_URL (no fallback to sqlite3)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600
    )
}

# Optional Redis support for dev
if config('REDIS_URL', default=None):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL'),
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

# Console backend for emails in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS settings for local frontend devs
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_ALL_ORIGINS = True  # For dev only, allows all origins
