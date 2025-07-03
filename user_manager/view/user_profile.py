from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
import logging

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


class UserProfileView:
    """View class for UserProfile API endpoints"""

    @staticmethod
    @api_view(['GET'])
    def get_profile(request, profile_uuid):
        """Get user profile information by profile UUID"""
        try:
            # Initialize service
            profile_service = UserProfileService(profile_uuid=profile_uuid)

            # Process get profile
            profile = profile_service.process_get_profile()

            # Serialize response
            serializer = UserProfileSerializer(profile)

            return Response({
                'success': True,
                'data': serializer.data
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error retrieving user profile with UUID {profile_uuid}: {e}")
            return Response({
                'success': False,
                'error': f'Unable to retrieve user profile with UUID {profile_uuid}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['PUT'])
    def update_profile(request, profile_uuid):
        """Update user profile information by profile UUID"""
        try:
            # Initialize service
            profile_service = UserProfileService(profile_uuid=profile_uuid)

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

                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'data': response_serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating user profile with UUID {profile_uuid}: {e}")
            return Response({
                'success': False,
                'error': f'Unable to update user profile with UUID {profile_uuid}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['PUT'])
    def change_password(request, profile_uuid):
        """Change user password by profile UUID"""
        try:
            # Initialize service
            profile_service = UserProfileService(profile_uuid=profile_uuid)

            # Use the existing serializer for backward compatibility
            serializer = ChangePasswordSerializer(data=request.data)

            if serializer.is_valid():
                current_password = serializer.validated_data['current_password']
                new_password = serializer.validated_data['new_password']

                # Verify current password
                if not profile_service.profile.check_password(current_password):
                    return Response({
                        'success': False,
                        'error': 'Current password is incorrect'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Process password change
                profile_service.process_change_password(current_password, new_password)

                return Response({
                    'success': True,
                    'message': 'Password changed successfully'
                })
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error changing password for profile UUID {profile_uuid}: {e}")
            return Response({
                'success': False,
                'error': f'Unable to change password for profile UUID {profile_uuid}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

                return Response({
                    'success': True,
                    'message': 'Profile created successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error creating user profile: {e}")
            return Response({
                'success': False,
                'error': 'Unable to create user profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

            return Response({
                'success': True,
                'count': len(profiles),
                'total': total_count,
                'data': serializer.data
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error listing user profiles: {e}")
            return Response({
                'success': False,
                'error': 'Unable to retrieve user profiles'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['DELETE'])
    def delete_profile(request, profile_uuid):
        """Delete user profile (soft delete)"""
        try:
            # Initialize service
            profile_service = UserProfileService(profile_uuid=profile_uuid)

            # Process delete
            profile_service.process_delete_profile()

            return Response({
                'success': True,
                'message': 'Profile deleted successfully'
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error deleting user profile with UUID {profile_uuid}: {e}")
            return Response({
                'success': False,
                'error': f'Unable to delete user profile with UUID {profile_uuid}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    def get_ai_context(request, profile_uuid):
        """Get AI context data for user profile"""
        try:
            # Initialize service
            profile_service = UserProfileService(profile_uuid=profile_uuid)

            # Get AI context
            ai_context = profile_service.get_ai_context()

            return Response({
                'success': True,
                'data': ai_context
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting AI context for profile UUID {profile_uuid}: {e}")
            return Response({
                'success': False,
                'error': f'Unable to get AI context for profile UUID {profile_uuid}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    def get_profile_summary(request, profile_uuid):
        """Get summarized profile information"""
        try:
            # Initialize service
            profile_service = UserProfileService(profile_uuid=profile_uuid)

            # Get profile summary
            summary = profile_service.get_profile_summary()

            return Response({
                'success': True,
                'data': summary
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting profile summary for UUID {profile_uuid}: {e}")
            return Response({
                'success': False,
                'error': f'Unable to get profile summary for UUID {profile_uuid}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function-based views for backward compatibility with URLs
def get_user_profile(request, profile_uuid):
    """Function wrapper for get profile"""
    return UserProfileView.get_profile(request, profile_uuid)

def update_user_profile(request, profile_uuid):
    """Function wrapper for update profile"""
    return UserProfileView.update_profile(request, profile_uuid)

def change_password(request, profile_uuid):
    """Function wrapper for change password"""
    return UserProfileView.change_password(request, profile_uuid)

def create_user_profile(request):
    """Function wrapper for create profile"""
    return UserProfileView.create_profile(request)

def list_user_profiles(request):
    """Function wrapper for list profiles"""
    return UserProfileView.list_profiles(request)

def delete_user_profile(request, profile_uuid):
    """Function wrapper for delete profile"""
    return UserProfileView.delete_profile(request, profile_uuid)

def get_user_ai_context(request, profile_uuid):
    """Function wrapper for get AI context"""
    return UserProfileView.get_ai_context(request, profile_uuid)

def get_user_profile_summary(request, profile_uuid):
    """Function wrapper for get profile summary"""
    return UserProfileView.get_profile_summary(request, profile_uuid)