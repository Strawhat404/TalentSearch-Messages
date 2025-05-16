from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# API Documentation URLs
api_docs_urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(
        url_name='schema',
        permission_classes=[permissions.AllowAny],
    ), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(
        url_name='schema',
        permission_classes=[permissions.AllowAny],
    ), name='redoc'),
]

# Main URL patterns
urlpatterns = [
    # Root URL redirects to API docs
    path('', RedirectView.as_view(url='/api/docs/swagger/', permanent=True)),
    
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('authapp.urls')),
    path('api/messages/', include('messaging.urls')),
    path('api/news/', include('news.urls')),
    path('api/adverts/', include('adverts.urls')),
    path('api/auth/profile/', include('userprofile.urls')),
    path('api/user_gallery/', include('usergallery.urls')),
    path('api/feed_posts/', include('feed_posts.urls', namespace='feed_posts')),
    path('api/jobs/', include('jobs.urls')),
    path('api/feed_likes/', include('feed_likes.urls', namespace='feed_likes')),
    path('api/feed_comments/', include('feed_comments.urls')),
    path('api/comment_likes/', include('comment_likes.urls')),
    # API Documentation
    path('api/docs/', include(api_docs_urlpatterns)),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
