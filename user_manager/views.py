from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import logging
import json
import os

from .models import UserProfile
from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    UserProfileCreateSerializer
)

# Set up logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_user_profile(request, profile_uuid):
    """
    Get user profile information by profile UUID
    """
    try:
        # Get user profile by UUID
        profile = get_object_or_404(UserProfile, profile_uuid=profile_uuid)

        serializer = UserProfileSerializer(profile)
        logger.info(f"Retrieved profile for user: {profile.username} (UUID: {profile_uuid})")

        return Response({
            'success': True,
            'data': serializer.data
        })

    except Exception as e:
        logger.error(f"Error retrieving user profile with UUID {profile_uuid}: {e}")
        return Response(
            {'error': f'Unable to retrieve user profile with UUID {profile_uuid}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def update_user_profile(request, profile_uuid):
    """
    Update user profile information by profile UUID
    """
    try:
        # Get user profile by UUID
        profile = get_object_or_404(UserProfile, profile_uuid=profile_uuid)

        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            logger.info(f"Updated profile for user: {profile.username} (UUID: {profile_uuid})")

            # Return updated profile data
            response_serializer = UserProfileSerializer(profile)
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

    except Exception as e:
        logger.error(f"Error updating user profile with UUID {profile_uuid}: {e}")
        return Response(
            {'error': f'Unable to update user profile with UUID {profile_uuid}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def change_password(request, profile_uuid):
    """
    Change user password by profile UUID
    """
    try:
        # Get user profile by UUID
        profile = get_object_or_404(UserProfile, profile_uuid=profile_uuid)

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            # Verify current password
            if not profile.check_password(current_password):
                return Response({
                    'success': False,
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update password
            profile.set_password(new_password)
            profile.save()

            logger.info(f"Password changed for user: {profile.username} (UUID: {profile_uuid})")

            return Response({
                'success': True,
                'message': 'Password changed successfully'
            })
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error changing password for profile UUID {profile_uuid}: {e}")
        return Response(
            {'error': f'Unable to change password for profile UUID {profile_uuid}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_user_profile(request):
    """
    Create a new user profile (for testing purposes)
    """
    try:
        serializer = UserProfileCreateSerializer(data=request.data)

        if serializer.is_valid():
            profile = serializer.save()
            logger.info(f"Created new profile for user: {profile.username} (UUID: {profile.profile_uuid})")

            # Return created profile data
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

    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return Response(
            {'error': 'Unable to create user profile'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def list_user_profiles(request):
    """
    List all user profiles (for testing/admin purposes)
    """
    try:
        profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(profiles, many=True)

        logger.info(f"Retrieved {profiles.count()} user profiles")

        return Response({
            'success': True,
            'count': profiles.count(),
            'data': serializer.data
        })

    except Exception as e:
        logger.error(f"Error listing user profiles: {e}")
        return Response(
            {'error': 'Unable to retrieve user profiles'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )