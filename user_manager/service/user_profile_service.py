import logging
from typing import Optional, List, Dict, Any
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from base.service.base_service import AbstractBaseService
from ..models.user_profile import UserProfile


class UserProfileService(AbstractBaseService):
    """Service class for UserProfile business logic"""

    def __init__(self, user_profile_uuid: str = None):
        super().__init__()
        """Initialize service with optional profile UUID"""
        self.user_profile_uuid = user_profile_uuid
        self.profile = None
        self.logger = logging.getLogger(__name__)

        if user_profile_uuid:
            self.profile = self._get_profile_by_uuid(user_profile_uuid)

    def _set_model(self) -> list:
        return ['user_manager', 'UserProfile']

    def _get_profile_by_uuid(self, user_profile_uuid: str) -> UserProfile:
        """Get profile by UUID or raise 404"""
        try:
            return get_object_or_404(UserProfile, user_profile_uuid=user_profile_uuid)
        except Exception as e:
            self.logger.error(f"Error retrieving user profile: {e}")
            raise

    def process_get_profile(self) -> UserProfile:
        """Get user profile information"""
        if not self.profile:
            raise ValidationError("Profile not found")

        username = self.profile.user_uuid.username if self.profile.user_uuid else None
        self.logger.info(f"Retrieved profile for user: {username} (UUID: {self.user_profile_uuid})")
        return self.profile

    def process_create_profile(self, validated_data: Dict[str, Any]) -> UserProfile:
        """Create new user profile"""
        try:
            # Extract password from validated data
            password = validated_data.pop('password', None)

            # Create profile instance
            profile = UserProfile(**validated_data)

            # Set password if provided
            if password:
                profile.set_password(password)

            profile.save()

            username = profile.user_uuid.username if profile.user_uuid else None
            self.logger.info(f"Created new profile for user: {username} (UUID: {self.user_profile_uuid})")
            return profile

        except Exception as e:
            self.logger.error(f"Error creating user profile: {e}")
            raise ValidationError(f"Unable to create user profile: {str(e)}")

    def process_update_profile(self, validated_data: Dict[str, Any]) -> UserProfile:
        """Update user profile information"""
        if not self.profile:
            raise ValidationError("Profile not found")

        try:
            # Update profile fields
            for field, value in validated_data.items():
                if hasattr(self.profile, field):
                    setattr(self.profile, field, value)

            self.profile.save()

            username = self.profile.user_uuid.username if self.profile.user_uuid else None
            self.logger.info(f"Updated profile for user: {username} (UUID: {self.user_profile_uuid})")
            return self.profile

        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            raise ValidationError(f"Unable to update user profile: {str(e)}")

    def process_change_password(self, current_password: str, new_password: str) -> bool:
        """Change user password"""
        if not self.profile:
            raise ValidationError("Profile not found")

        try:
            # Verify current password
            if not self.profile.check_password(current_password):
                raise ValidationError("Current password is incorrect")

            # Update password
            self.profile.set_password(new_password)
            self.profile.save()

            username = self.profile.user_uuid.username if self.profile.user_uuid else None
            self.logger.info(f"Password changed for user: {username} (UUID: {self.user_profile_uuid})")
            return True

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            raise ValidationError(f"Unable to change password: {str(e)}")

    def process_delete_profile(self) -> bool:
        """Delete user profile (soft delete)"""
        if not self.profile:
            raise ValidationError("Profile not found")

        try:
            username = self.profile.user_uuid.username if self.profile.user_uuid else None
            self.profile.delete()

            self.logger.info(f"Deleted profile for user: {username} (UUID: {self.user_profile_uuid})")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting user profile: {e}")
            raise ValidationError(f"Unable to delete user profile: {str(e)}")

    @staticmethod
    def process_list_profiles(filters: Dict[str, Any] = None) -> List[UserProfile]:
        """List user profiles with optional filters"""
        logger = logging.getLogger(__name__)

        try:
            queryset = UserProfile.objects.all()

            if filters:
                # Apply search filter
                search = filters.get('search')
                if search:
                    queryset = queryset.filter(
                        Q(username__icontains=search) |
                        Q(email__icontains=search) |
                        Q(address__icontains=search) |
                        Q(interests__icontains=search)
                    )

                # Apply ordering
                ordering = filters.get('ordering', '-created_at')
                if ordering:
                    queryset = queryset.order_by(ordering)

                # Apply pagination
                offset = filters.get('offset', 0)
                limit = filters.get('limit', 20)
                queryset = queryset[offset:offset + limit]

            profiles = list(queryset)
            logger.info(f"Retrieved {len(profiles)} user profiles")
            return profiles

        except Exception as e:
            logger.error(f"Error listing user profiles: {e}")
            raise ValidationError(f"Unable to retrieve user profiles: {str(e)}")

    @staticmethod
    def process_get_profile_count(filters: Dict[str, Any] = None) -> int:
        """Get total count of profiles with filters"""
        try:
            queryset = UserProfile.objects.all()

            if filters:
                search = filters.get('search')
                if search:
                    queryset = queryset.filter(
                        Q(username__icontains=search) |
                        Q(email__icontains=search) |
                        Q(address__icontains=search) |
                        Q(interests__icontains=search)
                    )

            return queryset.count()

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting user profiles: {e}")
            return 0

    def get_ai_context(self) -> Dict[str, Any]:
        """Generate AI context data for current profile"""
        if not self.profile:
            raise ValidationError("Profile not found")

        return self.profile.get_ai_context()

    def validate_profile_ownership(self, user_uuid: str) -> bool:
        """Validate if user owns this profile (for future authentication)"""
        if not self.profile:
            return False

        # This would typically check against a User model relation
        # For now, just return True as we don't have authentication yet
        return True

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get summarized profile information"""
        if not self.profile:
            raise ValidationError("Profile not found")

        return {
            'user_profile_uuid': str(self.profile.user_profile_uuid),
            'username': self.profile.user_uuid.username if self.profile.user_uuid else None,
            'email': self.profile.user_uuid.email if self.profile.user_uuid else None,
            'address': self.profile.address,
            'interests': self.profile.interests,
            'created_at': self.profile.created_at.isoformat() if self.profile.created_at else None,
            'preferences_count': len([
                pref for pref in [
                    self.profile.likes,
                    self.profile.dislikes,
                    self.profile.allergies,
                    self.profile.price_sensitivity
                ] if pref
            ])
        }

    @staticmethod
    def check_email_exists(email: str, exclude_uuid: str = None) -> bool:
        """Check if email already exists"""
        queryset = UserProfile.objects.filter(email=email)
        if exclude_uuid:
            queryset = queryset.exclude(user_profile_uuid=exclude_uuid)
        return queryset.exists()

    @staticmethod
    def get_profiles_by_preferences(preferences: Dict[str, Any]) -> List[UserProfile]:
        """Get profiles matching certain preferences (for analytics)"""
        try:
            queryset = UserProfile.objects.all()

            # Filter by travel preferences
            if 'passport_nationality' in preferences:
                queryset = queryset.filter(passport_nationality=preferences['passport_nationality'])

            if 'seat_preference' in preferences:
                queryset = queryset.filter(seat_preference=preferences['seat_preference'])

            if 'likes' in preferences:
                likes = preferences['likes']
                if isinstance(likes, list):
                    for like in likes:
                        queryset = queryset.filter(likes__contains=[like])

            return list(queryset)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error filtering profiles by preferences: {e}")
            return []