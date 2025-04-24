from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions  # ✅ This was missing
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

schema_view = get_schema_view(
   openapi.Info(
      title="TalentSearch API",
      default_version='v1',
      description="API documentation for TalentSearch platform",
      terms_of_service="https://yourcompany.com/terms/",
      contact=openapi.Contact(email="dev@yourcompany.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('messages/', include('messaging.urls')),
    path('api/news/', include('news.urls')),
    path('api/adverts/', include('adverts.urls')),
    path('api/auth/', include('authapp.urls')),
   
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
