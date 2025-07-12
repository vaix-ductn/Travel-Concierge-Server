from django.urls import path
from .view import user_profile
from .view.plan import create_plan, get_plan, update_plan, delete_plan, list_plans

app_name = 'user_manager'

urlpatterns = [
    # Profile management endpoints (when accessed via /api/user_manager/)
    path('profiles/', user_profile.list_user_profiles, name='list_profiles'),  # List all profiles
    path('profile/<uuid:user_profile_uuid>/', user_profile.get_user_profile, name='get_profile'),  # Get specific profile
    path('profile/<uuid:user_profile_uuid>/update/', user_profile.update_user_profile, name='update_profile'),  # Update specific profile
    path('profile/create/', user_profile.create_user_profile, name='create_profile'),  # Create new profile
    path('profile/<uuid:user_profile_uuid>/delete/', user_profile.delete_user_profile, name='delete_profile'),  # Delete specific profile
    path('profile/<uuid:user_profile_uuid>/ai-context/', user_profile.get_user_ai_context, name='get_ai_context'),  # Get AI context for profile
    path('profile/<uuid:user_profile_uuid>/summary/', user_profile.get_user_profile_summary, name='get_profile_summary'),  # Get profile summary
    # Plan endpoints
    path('plan/<uuid:user_uuid>/create/', create_plan, name='create_plan'),
    path('plan/<uuid:plan_uuid>/', get_plan, name='get_plan'),
    path('plan/<uuid:plan_uuid>/update/', update_plan, name='update_plan'),
    path('plan/<uuid:plan_uuid>/delete/', delete_plan, name='delete_plan'),
    path('plan/<uuid:user_uuid>/list/', list_plans, name='list_plans'),
]