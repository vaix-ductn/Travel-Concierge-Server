"""URL configuration for travel concierge project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Travel Concierge API",
        default_version='v1',
        description="API documentation for Travel Concierge application",
        contact=openapi.Contact(email="dev@travelconcierge.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('user_manager.urls')),  # Authentication APIs (moved to user_manager)
    path('api/user_manager/', include('user_manager.urls')),  # User profile APIs
    path('api/agent/', include('travel_concierge.urls')),  # Travel concierge APIs (AI Agent, recommendations, etc.)

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)