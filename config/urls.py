"""URL configuration for travel concierge project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .swagger_test import swagger_test, test_schema_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('user_manager.urls')),  # Authentication APIs
    path('api/user_manager/', include('user_manager.urls')),  # User profile APIs
    path('api/agent/', include('travel_concierge.urls')),  # Travel concierge APIs (AI Agent, recommendations, etc.)

    # Test endpoint
    path('swagger-test/', swagger_test, name='swagger-test'),

    # API Documentation
    path('swagger/', test_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', test_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', test_schema_view.without_ui(cache_timeout=0), name='schema-json'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)