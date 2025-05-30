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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from userprofile.views import ChoiceDataView

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
    return JsonResponse({"status": "healthy"})

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
    path('api/choices/', ChoiceDataView.as_view(), name='choice_data'),
    path('api/user_gallery/', include('usergallery.urls')),
    path('api/feed_posts/', include('feed_posts.urls', namespace='feed_posts')),
    path('api/jobs/', include('jobs.urls')),
    path('api/feed_likes/', include('feed_likes.urls', namespace='feed_likes')),
    path('api/feed_comments/', include('feed_comments.urls')),
    path('api/comment_likes/', include('comment_likes.urls')),
    path('api/rental/', include('rental_items.urls')),
    path('api/ratings/', include('rental_ratings.urls')),
    path('api/user_ratings/', include('user_ratings.urls')),
    path('api/health/', health_check, name='health_check'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
