"""
ASGI config for talentsearch project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from whitenoise import ASGIStaticFilesWrapper

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentsearch.settings.prod')

application = get_asgi_application()

# Serve media files with WhiteNoise in production
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
media_path = os.path.join(BASE_DIR, 'media')

# WhiteNoise's ASGI wrapper for static files (works for media too)
application = ASGIStaticFilesWrapper(application, static_root=media_path, static_prefix='/media/')
