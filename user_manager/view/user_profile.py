from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
import logging
from django.views.decorators.csrf import csrf_exempt
from base.view.custom_view_set import CustomViewSet
from base.response.utils import api_response_success, api_response_error
from ..service.user_profile_service import UserProfileService
from ..serializers.user_profile_serializer import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    UserProfileCreateSerializer
)
from ..validation.user_profile_validation import (
    UserProfileUpdateValidation,
    UserProfileCreateValidation,
    ChangePasswordValidation,
    UserProfileListValidation
)
from ..permission.user_profile_permission import UserProfilePermission


class UserProfileView(CustomViewSet):
    permission_classes = [UserProfilePermission]
    """View class for UserProfile API endpoints"""

    @staticmethod
    @api_view(['GET'])
    def get_profile(request, user_profile_uuid):
        """Get user profile information by profile UUID"""
        try:
            # Initialize service
            profile_service = UserProfileService(user_profile_uuid=user_profile_uuid)

            # Process get profile
            profile = profile_service.process_get_profile()

            # Serialize response
            serializer = UserProfileSerializer(profile)

            return api_response_success(data=serializer.data)

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error retrieving user profile with UUID {user_profile_uuid}: {e}")
            return api_response_error(msg=f'Unable to retrieve user profile with UUID {user_profile_uuid}')

    @staticmethod
    @api_view(['PUT'])
    def update_profile(request, user_profile_uuid):
        """Update user profile information by profile UUID"""
        try:
            # Initialize service
            profile_service = UserProfileService(user_profile_uuid=user_profile_uuid)

            # Use the existing serializer for backward compatibility
            serializer = UserProfileUpdateSerializer(
                profile_service.profile,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                # Process update
                updated_profile = profile_service.process_update_profile(serializer.validated_data)

                # Serialize response
                response_serializer = UserProfileSerializer(updated_profile)

                return api_response_success(msg='Profile updated successfully', data=response_serializer.data)
            else:
                return api_response_error(msg='Validation error', data=serializer.errors)

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating user profile with UUID {user_profile_uuid}: {e}")
            return api_response_error(msg=f'Unable to update user profile with UUID {user_profile_uuid}')

    @staticmethod
    @api_view(['PUT'])
    def change_password(request, user_profile_uuid):
        """Change user password by profile UUID"""
        try:
            # Đã chuyển sang auth_view.ChangePasswordView, bỏ logic cũ
            return api_response_error(msg='This endpoint is deprecated. Please use /api/auth/change-password/')
        except Exception:
            return api_response_error(msg='This endpoint is deprecated. Please use /api/auth/change-password/')

    @staticmethod
    @api_view(['POST'])
    def create_profile(request):
        """Create a new user profile"""
        try:
            # Use the existing serializer for backward compatibility
            serializer = UserProfileCreateSerializer(data=request.data)

            if serializer.is_valid():
                # Create profile using serializer
                profile = serializer.save()

                # Serialize response
                response_serializer = UserProfileSerializer(profile)

                return api_response_success(msg='Profile created successfully', data=response_serializer.data)
            else:
                return api_response_error(msg='Validation error', data=serializer.errors)

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error creating user profile: {e}")
            return api_response_error(msg='Unable to create user profile')

    @staticmethod
    @api_view(['GET'])
    def list_profiles(request):
        """List all user profiles with optional filters"""
        try:
            # Simple implementation for backward compatibility
            profiles = UserProfileService.process_list_profiles()
            total_count = UserProfileService.process_get_profile_count()

            # Serialize response
            serializer = UserProfileSerializer(profiles, many=True)

            return api_response_success(data={
                'count': len(profiles),
                'total': total_count,
                'data': serializer.data
            })

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error listing user profiles: {e}")
            return api_response_error(msg='Unable to retrieve user profiles')

    @staticmethod
    @api_view(['DELETE'])
    def delete_profile(request, user_profile_uuid):
        """Delete user profile (soft delete)"""
        try:
            # Initialize service
            profile_service = UserProfileService(user_profile_uuid=user_profile_uuid)

            # Process delete
            profile_service.process_delete_profile()

            return api_response_success(msg='Profile deleted successfully')

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error deleting user profile with UUID {user_profile_uuid}: {e}")
            return api_response_error(msg=f'Unable to delete user profile with UUID {user_profile_uuid}')

    @staticmethod
    @api_view(['GET'])
    def get_ai_context(request, user_profile_uuid):
        """Get AI context data for user profile"""
        try:
            # Initialize service
            profile_service = UserProfileService(user_profile_uuid=user_profile_uuid)

            # Get AI context
            ai_context = profile_service.get_ai_context()

            return api_response_success(data=ai_context)

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting AI context for profile UUID {user_profile_uuid}: {e}")
            return api_response_error(msg=f'Unable to get AI context for profile UUID {user_profile_uuid}')

    @staticmethod
    @api_view(['GET'])
    def get_profile_summary(request, user_profile_uuid):
        """Get summarized profile information"""
        try:
            # Initialize service
            profile_service = UserProfileService(user_profile_uuid=user_profile_uuid)

            # Get profile summary
            summary = profile_service.get_profile_summary()

            return api_response_success(data=summary)

        except ValidationError as e:
            return api_response_error(msg=str(e))

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting profile summary for UUID {user_profile_uuid}: {e}")
            return api_response_error(msg=f'Unable to get profile summary for UUID {user_profile_uuid}')


# Function-based views for backward compatibility with URLs
@csrf_exempt
def get_user_profile(request, user_profile_uuid):
    """Function wrapper for get profile"""
    return UserProfileView.get_profile(request, user_profile_uuid)

@csrf_exempt
def update_user_profile(request, user_profile_uuid):
    """Function wrapper for update profile"""
    return UserProfileView.update_profile(request, user_profile_uuid)

@csrf_exempt
def create_user_profile(request):
    """Function wrapper for create profile"""
    return UserProfileView.create_profile(request)

@csrf_exempt
def list_user_profiles(request):
    """Function wrapper for list profiles"""
    return UserProfileView.list_profiles(request)

@csrf_exempt
def delete_user_profile(request, user_profile_uuid):
    """Function wrapper for delete profile"""
    return UserProfileView.delete_profile(request, user_profile_uuid)

@csrf_exempt
def get_user_ai_context(request, user_profile_uuid):
    """Function wrapper for get AI context"""
    return UserProfileView.get_ai_context(request, user_profile_uuid)

@csrf_exempt
def get_user_profile_summary(request, user_profile_uuid):
    """Function wrapper for get profile summary"""
    return UserProfileView.get_profile_summary(request, user_profile_uuid)