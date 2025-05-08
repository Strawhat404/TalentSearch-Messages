"""
Development settings for TalentSearch project.
"""

from .base import *
import dj_database_url
from decouple import config

DEBUG = config('DEBUG', cast=bool, default=True)

SECRET_KEY = config('SECRET_KEY', default='insecure-dev-key')

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

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

# Console backend for emails in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
