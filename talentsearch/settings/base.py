"""
Base settings for TalentSearch project.
"""



import os
from pathlib import Path
import environ
import sys

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Set base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read from .env file if it exists
if os.path.exists(os.path.join(BASE_DIR, ".env")):
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Security
SECRET_KEY = env("SECRET_KEY", default="django-insecure-key-for-development-only")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = [
    'talentsearch-messages-uokp.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'drf_spectacular',
    'taggit',
    'corsheaders',
    'django_filters',
    'rest_framework_simplejwt.token_blacklist',

    # Custom apps
    'authapp',
    'feed_posts',
    'messaging',
    'news',
    'adverts',
    'userprofile',
    'usergallery',
    'jobs',
    'feed_likes',
    'feed_comments',
    'comment_likes',
    'rental_items',
    'rental_ratings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'talentsearch.middleware.AdminRateLimitMiddleware',
    'authapp.middleware.SessionExpirationMiddleware',
]

ROOT_URLCONF = 'talentsearch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'talentsearch.wsgi.application'

# Database
DATABASES = {
    'default': env.db(),
}

# Caching (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
        }
    }
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Custom user model
AUTH_USER_MODEL = 'authapp.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authapp.authentication.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
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
    },
    'TOKEN_EXPIRE_MINUTES': 60,  # Default token expiration (in minutes) if not overridden
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'authapp.models.User',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_BLACKLIST_ENABLED': True,
    'TOKEN_BLACKLIST_CHECK_ON_AUTHENTICATION': True,
}

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Password reset settings
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours in seconds
PASSWORD_RESET_TOKEN_TIMEOUT = 86400  # 24 hours in seconds

# API Schema
SPECTACULAR_SETTINGS = {
    'TITLE': 'TalentSearch API',
    'DESCRIPTION': 'API documentation for TalentSearch platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'tagsSorter': 'alpha',
        'operationsSorter': 'alpha',
    },
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication operations'},
        {'name': 'messages', 'description': 'Messaging system operations'},
        {'name': 'news', 'description': 'News management operations'},
        {'name': 'adverts', 'description': 'Advertisement management operations'},
    ],
    'SECURITY': [{'Token': []}],
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Token-based authentication. Format: Token <your_token>'
        }
    },
}

# Time and language
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True

# For development only (optional)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# Test Settings
if 'test' in sys.argv:
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'anon': '1000/minute',
        'user': '1000/minute',
        'test': '1000/minute',
        'auth': '1000/minute',
        'create': '1000/minute',  # Add create scope rate for tests
    }
    # Override JWT settings for tests
    SIMPLE_JWT.update({
        'ACCESS_TOKEN_LIFETIME': timedelta(seconds=1),
        'REFRESH_TOKEN_LIFETIME': timedelta(seconds=2),
        'ROTATE_REFRESH_TOKENS': True,
        'BLACKLIST_AFTER_ROTATION': True,
    })
    # Only use JWT authentication for tests
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
        'authapp.authentication.CustomJWTAuthentication',
    ]
