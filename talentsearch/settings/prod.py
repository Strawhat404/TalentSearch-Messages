"""
Production settings for TalentSearch project.
"""

from .base import *
import dj_database_url
from decouple import config, Csv
import os
import logging
from django.conf import settings
from datetime import timedelta
from django.core.files.storage import default_storage

# Set up logger early
logger = logging.getLogger("django")

print(">>> DJANGO_SETTINGS_MODULE:", os.environ.get("DJANGO_SETTINGS_MODULE"))

# Print ALLOWED_HOSTS for debugging
try:
    print(">>> ALLOWED_HOSTS (before):", repr(ALLOWED_HOSTS))
except Exception as e:
    print(">>> ALLOWED_HOSTS not set yet:", e)

# Temporary debug settings
DEBUG = False

ALLOWED_HOSTS = [
    'talentsearch-messages-1.onrender.com',
    'localhost',
    '127.0.0.1',
    '.onrender.com',  # This allows all subdomains of onrender.com
]

# Cloudinary settings for production
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Production Cloudinary configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUD_NAME'),
    'API_KEY': os.environ.get('API_KEY'),
    'API_SECRET': os.environ.get('API_SECRET'),
    # Production-specific settings
    'FOLDER': 'talentsearch/prod',
    'SECURE': True,  # Enable secure URLs for production
    'RESPONSIVE': True,
    'FORMAT': 'auto',
    'QUALITY': 'auto',
    # Production-optimized transformations
    'STATIC_TRANSFORMATIONS': {
        'thumbnail': {
            'width': 300,
            'height': 300,
            'crop': 'fill',
            'quality': 'auto',
            'fetch_format': 'auto'
        },
        'medium': {
            'width': 800,
            'height': 600,
            'crop': 'limit',
            'quality': 'auto',
            'fetch_format': 'auto'
        },
        'large': {
            'width': 1200,
            'height': 800,
            'crop': 'limit',
            'quality': 'auto',
            'fetch_format': 'auto'
        },
        'profile': {
            'width': 400,
            'height': 400,
            'crop': 'fill',
            'gravity': 'face',
            'quality': 'auto',
            'fetch_format': 'auto'
        }
    },
    # Video transformations for production
    'VIDEO_TRANSFORMATIONS': {
        'thumbnail': {
            'width': 300,
            'height': 300,
            'crop': 'fill',
            'video_codec': 'auto',
            'quality': 'auto'
        },
        'medium': {
            'width': 800,
            'height': 600,
            'crop': 'limit',
            'video_codec': 'auto',
            'quality': 'auto'
        },
        'preview': {
            'width': 400,
            'height': 300,
            'crop': 'limit',
            'video_codec': 'auto',
            'quality': 'auto',
            'duration': 10  # 10-second preview
        }
    },
    # Additional production optimizations
    'INVALIDATE': True,  # Invalidate CDN cache on updates
    'OVERWRITE': True,   # Overwrite existing files
    'RESOURCE_TYPE': 'auto',  # Auto-detect resource type
    'TYPE': 'upload',    # Upload type
}

# Validate Cloudinary configuration
cloud_name = CLOUDINARY_STORAGE.get('CLOUD_NAME')
api_key = CLOUDINARY_STORAGE.get('API_KEY')
api_secret = CLOUDINARY_STORAGE.get('API_SECRET')

if not all([cloud_name, api_key, api_secret]):
    print("❌ Cloudinary credentials not properly configured for production")
    print("   Please set CLOUD_NAME, API_KEY, and API_SECRET environment variables")
    # Fallback to local storage (not recommended for production)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    print("⚠️  Falling back to local file storage (not recommended for production)")
else:
    print("✅ Cloudinary configured for production")
    MEDIA_URL = ''

# Get SECRET_KEY from environment or generate a new one
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-development-key-please-change-in-production')

# Static files configuration
STATIC_ROOT = '/opt/render/project/src/staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_ROOT = os.path.join(BASE_DIR, 'media')
WHITENOISE_INDEX_FILE = True

# Cache configuration with fallback
REDIS_URL = config('REDIS_URL', default=None)
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'RETRY_ON_TIMEOUT': True,
                'MAX_CONNECTIONS': 1000,
                'CONNECTION_POOL_KWARGS': {'max_connections': 100},
                'IGNORE_EXCEPTIONS': True,  # Don't raise exceptions on Redis errors
            }
        }
    }
else:
    # Fallback to local memory cache if Redis is not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'auth': '10/minute',
        'create': '5/minute',
    },
    'DEFAULT_THROTTLE_CLASSES': [] if not REDIS_URL else [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'authapp': {  # Add this logger
            'handlers': ['console'],
            'level': 'ERROR',  # Only log errors in production
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Database configuration with fallback
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    try:
        # Parse the database URL manually to check for issues
        if DATABASE_URL.startswith('postgres://'):
            # Convert postgres:// to postgresql:// for newer versions
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")
        
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=True,  # Enable SSL for production
            )
        }
        
        # Log database configuration (without sensitive info)
        db_config = DATABASES['default']
        logger.info(f"Database configured: {db_config.get('ENGINE')} on {db_config.get('HOST')}:{db_config.get('PORT')}")
        
    except Exception as e:
        logger.error(f"Failed to configure database: {e}")
        # Fallback to your specific PostgreSQL config
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'talent_search',
                'USER': 'talent_user',
                'PASSWORD': 'Talent@12345',
                'HOST': 'localhost',
                'PORT': '5432',
                'OPTIONS': {
                    'sslmode': 'require',
                },
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
            }
        }
else:
    # Use your specific PostgreSQL config when no DATABASE_URL is provided
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'talent_search',
            'USER': 'talent_user',
            'PASSWORD': 'Talent@12345',
            'HOST': 'localhost',
            'PORT': '5432',
            'OPTIONS': {
                'sslmode': 'require',
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }

# Email config for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Authentication settings
AUTHENTICATION_BACKENDS = [
    'authapp.backends.EmailBackend',  # Custom email backend
]

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

CORS_ALLOWED_ORIGINS = [
    "https://talentdiscovery1.netlify.app",
    "https://myfrontend.com",
    "https://my-frontend.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

logger.warning(f"DJANGO STORAGE BACKEND: {default_storage.__class__}")

