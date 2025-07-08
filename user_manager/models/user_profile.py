import uuid
from django.db import models
import json


class UserProfile(models.Model):
    """User Profile model with travel preferences and basic information"""

    # Primary key using UUID4 with new field name
    user_profile_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Foreign key to User model for authentication data (temporary nullable)
    user = models.OneToOneField('user_manager.User', on_delete=models.CASCADE, related_name='profile', to_field='user_uuid', null=True, blank=True)

    # Basic profile information (from API spec)
    address = models.TextField()
    interests = models.TextField()
    avatar_url = models.URLField(max_length=500, null=True, blank=True)

    # Extended travel preferences (from itinerary_custom.json)
    passport_nationality = models.CharField(max_length=100, null=True, blank=True)
    seat_preference = models.CharField(max_length=50, null=True, blank=True)
    food_preference = models.TextField(null=True, blank=True)
    allergies = models.JSONField(default=list, null=True, blank=True)
    likes = models.JSONField(default=list, null=True, blank=True)
    dislikes = models.JSONField(default=list, null=True, blank=True)
    price_sensitivity = models.JSONField(default=list, null=True, blank=True)

    # Home information
    home_address = models.TextField(null=True, blank=True)
    local_prefer_mode = models.CharField(max_length=50, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} ({self.user.email})"
        return f"Profile {self.user_profile_uuid}"

    def to_dict(self):
        """Convert model instance to dictionary for API responses"""
        return {
            'user_profile_uuid': str(self.user_profile_uuid),
            'user_uuid': str(self.user.user_uuid) if self.user else None,
            'username': self.user.username if self.user else None,
            'email': self.user.email if self.user else None,
            'address': self.address,
            'interests': self.interests,
            'avatar_url': self.avatar_url,
            'passport_nationality': self.passport_nationality,
            'seat_preference': self.seat_preference,
            'food_preference': self.food_preference,
            'allergies': self.allergies,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'price_sensitivity': self.price_sensitivity,
            'home_address': self.home_address,
            'local_prefer_mode': self.local_prefer_mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_ai_context(self):
        """Generate user context data for AI Agent integration"""
        return {
            "user_scenario": {
                "user_profile_uuid": str(self.user_profile_uuid),
                "user_uuid": str(self.user.user_uuid) if self.user else None,
                "user_name": self.user.username if self.user else None,
                "user_email": self.user.email if self.user else None,
                "user_location": self.address,
                "user_interests": self.interests,
                "user_preferences": {
                    "passport_nationality": self.passport_nationality,
                    "seat_preference": self.seat_preference,
                    "food_preference": self.food_preference,
                    "likes": self.likes,
                    "dislikes": self.dislikes,
                    "price_sensitivity": self.price_sensitivity,
                    "home_address": self.home_address,
                    "local_prefer_mode": self.local_prefer_mode
                }
            }
        }