"""Authentication models for user management and token handling."""

import uuid
import json
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class User(models.Model):
    """User model for authentication system."""

    # Primary fields
    user_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    email = models.CharField(max_length=255, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)

    # Profile fields
    full_name = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    interests = models.JSONField(default=list, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    def set_password(self, raw_password):
        """Hash and set password."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if provided password matches stored hash."""
        return check_password(raw_password, self.password_hash)

    def update_last_login(self):
        """Update last login timestamp."""
        User.objects.filter(user_uuid=self.user_uuid).update(
            last_login=timezone.now()
        )

    def to_dict(self):
        """Convert user to dictionary for API responses."""
        return {
            'user_uuid': str(self.user_uuid),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'address': self.address,
            'interests': self.interests if self.interests else []
        }

    def get_auth_context(self):
        """Get user context for authentication responses."""
        return {
            'user_uuid': str(self.user_uuid),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name or self.username,
            'avatar_url': self.avatar_url,
            'address': self.address,
            'interests': self.interests if self.interests else []
        }


class UserToken(models.Model):
    """Model to track user tokens for logout functionality."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens', to_field='user_uuid')
    token_hash = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_tokens'
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"Token for {self.user.username} (expires: {self.expires_at})"

    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at

    def invalidate(self):
        """Invalidate the token."""
        self.is_active = False
        self.save()

    @classmethod
    def cleanup_expired_tokens(cls):
        """Clean up expired tokens."""
        expired_tokens = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        return count