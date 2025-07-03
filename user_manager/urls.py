from django.urls import path
from .view import user_profile
from .view.auth_view import LoginView, VerifyTokenView, LogoutView

app_name = 'user_manager'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/verify/', VerifyTokenView.as_view(), name='verify_token'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Profile management endpoints
    path('profiles/', user_profile.list_user_profiles, name='list_profiles'),  # List all profiles
    path('profile/<uuid:profile_uuid>/', user_profile.get_user_profile, name='get_profile'),  # Get specific profile
    path('profile/<uuid:profile_uuid>/update/', user_profile.update_user_profile, name='update_profile'),  # Update specific profile
    path('profile/<uuid:profile_uuid>/change-password/', user_profile.change_password, name='change_password'),  # Change password for specific profile
    path('profile/create/', user_profile.create_user_profile, name='create_profile'),  # Create new profile
]