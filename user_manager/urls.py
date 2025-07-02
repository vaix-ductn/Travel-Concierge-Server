from django.urls import path
from . import views

app_name = 'user_manager'

urlpatterns = [
    # Profile management endpoints
    path('profiles/', views.list_user_profiles, name='list_profiles'),  # List all profiles
    path('profile/<uuid:profile_uuid>/', views.get_user_profile, name='get_profile'),  # Get specific profile
    path('profile/<uuid:profile_uuid>/update/', views.update_user_profile, name='update_profile'),  # Update specific profile
    path('profile/<uuid:profile_uuid>/change-password/', views.change_password, name='change_password'),  # Change password for specific profile
    path('profile/create/', views.create_user_profile, name='create_profile'),  # Create new profile
]