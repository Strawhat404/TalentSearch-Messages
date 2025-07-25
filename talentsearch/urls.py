from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.db import connection
from django.db.utils import OperationalError
import os
from rest_framework.routers import DefaultRouter

schema_view = get_schema_view(
    openapi.Info(
        title="TalentSearch API",
        default_version='v1',
        description="API documentation for TalentSearch platform",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


@csrf_exempt
def health_check(request):
    """Enhanced health check that tests database connectivity"""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "environment": {
            "debug": settings.DEBUG,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "database_url_set": bool(os.environ.get('DATABASE_URL')),
        }
    }
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["database"] = "connected"
    except OperationalError as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["database"] = f"unknown error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return JsonResponse(health_status)

# Exempt all API views from CSRF
@method_decorator(csrf_exempt, name='dispatch')
class CSRFExemptTokenObtainPairView(TokenObtainPairView):
    pass

@method_decorator(csrf_exempt, name='dispatch')
class CSRFExemptTokenRefreshView(TokenRefreshView):
    pass

# Main URL patterns
urlpatterns = [
    # Root URL redirects to Swagger UI
    path('', RedirectView.as_view(url='/swagger/', permanent=True)),

    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('authapp.urls')),
    path('api/messages/', include('messaging.urls')),
    path('api/news/', include('news.urls')),
    path('api/adverts/', include('adverts.urls')),
    path('api/profile/', include('userprofile.urls')),
    path('api/user_gallery/', include('usergallery.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/rental/', include('rental_items.urls')),
    path('api/ratings/', include('rental_ratings.urls')),
    path('api/user_ratings/', include('user_ratings.urls')),
    path('api/contact/', include('contact_us.urls')),
    path('api/statistics/', include('platform_stat.urls')),
    path('api/payment/', include('payment.urls')),
    path('api/health/', health_check, name='health_check'),
    path('api/token/', CSRFExemptTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CSRFExemptTokenRefreshView.as_view(), name='token_refresh'),
    path('api/feed/', include('feed.urls')),
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)