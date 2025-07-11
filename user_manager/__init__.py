"""
User Manager Application

A Django app that provides comprehensive user management functionality including:
- User authentication (login, logout, token verification)
- User profile management
- JWT token management with blacklisting
- Rate limiting and security features
- Permission and validation systems

This app follows a clean architecture pattern with separation of concerns:
- Models: Data layer (User, UserToken, UserProfile)
- Services: Business logic layer (AuthService, UserProfileService, TokenService)
- Views: Presentation layer (LoginView, VerifyTokenView, LogoutView, UserProfileView)
- Serializers: Data transformation layer
- Validation: Input validation and business rules
- Permissions: Access control layer
"""

# App configuration
default_app_config = 'user_manager.apps.UserManagerConfig'

__version__ = '1.0.0'
__author__ = 'Travel Concierge Team'

# Note: Imports are intentionally minimal here to avoid Django AppRegistryNotReady errors
# Import specific components as needed in your code:
# from user_manager.models import User, UserToken, UserProfile
# from user_manager.service import AuthService, TokenService
# from user_manager.view import LoginView, VerifyTokenView, LogoutView
# from user_manager.serializers import LoginSerializer, UserSerializer
# from user_manager.permission import AuthPermission, UserProfilePermission