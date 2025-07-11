from django.urls import path
from .view import user_profile

app_name = 'user_manager'

urlpatterns = [
    # Profile management endpoints (when accessed via /api/user_manager/)
    path('profiles/', user_profile.list_user_profiles, name='list_profiles'),  # List all profiles
    path('profile/<uuid:user_profile_uuid>/', user_profile.get_user_profile, name='get_profile'),  # Get specific profile
    path('profile/<uuid:user_profile_uuid>/update/', user_profile.update_user_profile, name='update_profile'),  # Update specific profile
    path('profile/<uuid:user_profile_uuid>/change-password/', user_profile.change_password, name='change_password'),  # Change password for specific profile
    path('profile/create/', user_profile.create_user_profile, name='create_profile'),  # Create new profile
    path('profile/<uuid:user_profile_uuid>/delete/', user_profile.delete_user_profile, name='delete_profile'),  # Delete specific profile
    path('profile/<uuid:user_profile_uuid>/ai-context/', user_profile.get_user_ai_context, name='get_ai_context'),  # Get AI context for profile
    path('profile/<uuid:user_profile_uuid>/summary/', user_profile.get_user_profile_summary, name='get_profile_summary'),  # Get profile summary
]