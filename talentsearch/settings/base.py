"""
Base settings for TalentSearch project.
"""

import os
from pathlib import Path
import environ
import sys
from datetime import timedelta

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
    'talentsearch-messages-1.onrender.com',
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
    'taggit',
    'corsheaders',
    'django_filters',
    'rest_framework_simplejwt.token_blacklist',
    'cloudinary',
    'cloudinary_storage',

    # Custom apps
    'authapp',
    'messaging',
    'news',
    'adverts',
    'userprofile',
    'usergallery',
    'jobs',
    'rental_items',
    'rental_ratings',
    'user_ratings',
    'contact_us',
    'platform_stat',
    'payment',
    'feed',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authapp.views.TokenAuthenticationMiddleware',
    'authapp.middleware.AutoTokenRefreshMiddleware',  # Add new middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'talentsearch.middleware.AdminRateLimitMiddleware',
    'talentsearch.middleware.CSRFExemptMiddleware',
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
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='dev@example.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='dev_password')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='dev@example.com')
CONTACT_RECIPIENT_EMAIL = env('CONTACT_RECIPIENT_EMAIL', default='dev@example.com')

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = ''  # Not needed for Cloudinary
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUD_NAME', default='dummy_cloud_name'),
    'API_KEY': env('API_KEY', default='dummy_api_key'),
    'API_SECRET': env('API_SECRET', default='dummy_api_secret'),
    # Additional Cloudinary settings for better performance
    'STATIC_TRANSFORMATIONS': {
        'thumbnail': {
            'width': 300,
            'height': 300,
            'crop': 'fill',
            'quality': 'auto'
        },
        'medium': {
            'width': 800,
            'height': 600,
            'crop': 'limit',
            'quality': 'auto'
        },
        'large': {
            'width': 1200,
            'height': 800,
            'crop': 'limit',
            'quality': 'auto'
        }
    },
    # Video transformations
    'VIDEO_TRANSFORMATIONS': {
        'thumbnail': {
            'width': 300,
            'height': 300,
            'crop': 'fill',
            'video_codec': 'auto'
        },
        'medium': {
            'width': 800,
            'height': 600,
            'crop': 'limit',
            'video_codec': 'auto'
        }
    },
    # Folder structure for better organization
    'FOLDER': 'talentsearch',
    # Enable secure URLs
    'SECURE': True,
    # Enable responsive images
    'RESPONSIVE': True,
    # Enable automatic format optimization
    'FORMAT': 'auto',
    # Enable automatic quality optimization
    'QUALITY': 'auto',
}

# Custom user model
AUTH_USER_MODEL = 'authapp.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authapp.authentication.BlacklistCheckingJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
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
    },
}

# JWT Settings - Remove the duplicate and use proper token lifetimes
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # 1 hour for security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # 30 days for long-term sessions
    'ROTATE_REFRESH_TOKENS': True,  # Generate new refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old refresh tokens
    'UPDATE_LAST_LOGIN': True,  # Update last login timestamp
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    # Additional settings for better security
    'ACCESS_TOKEN_REFRESH_THRESHOLD': timedelta(minutes=5),  # Refresh 5 minutes before expiry
    'REFRESH_TOKEN_REFRESH_THRESHOLD': timedelta(hours=1),  # Refresh refresh token 1 hour before expiry
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
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]

# Authentication settings
AUTHENTICATION_BACKENDS = [
    'authapp.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',  # keep default as fallback
]

# prod.py (for stricter security)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
