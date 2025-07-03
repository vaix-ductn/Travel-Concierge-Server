"""URL configuration for travel concierge project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user_manager/', include('user_manager.urls')),  # User profile APIs
    path('api/agent/', include('travel_concierge.urls')),  # Travel concierge APIs (AI Agent, recommendations, etc.)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)