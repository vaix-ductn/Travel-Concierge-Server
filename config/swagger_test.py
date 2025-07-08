from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def swagger_test(request):
    """Test view to check if Swagger is working"""
    return JsonResponse({
        'message': 'Swagger test endpoint is working',
        'swagger_url': '/swagger/',
        'redoc_url': '/redoc/',
        'schema_json_url': '/swagger.json'
    })

# Alternative schema view without authentication
test_schema_view = get_schema_view(
    openapi.Info(
        title="Travel Concierge API",
        default_version='v1',
        description="API documentation for Travel Concierge application",
        contact=openapi.Contact(email="dev@travelconcierge.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)