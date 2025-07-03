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
    id = models.CharField(max_length=50, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:10]}")
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

    # Security fields
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)

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

    def is_locked(self):
        """Check if account is currently locked."""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False

    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration."""
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save()

    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()

    def increment_failed_attempts(self):
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save()

    def reset_failed_attempts(self):
        """Reset failed login attempts on successful login."""
        self.failed_login_attempts = 0
        self.last_login = timezone.now()
        self.save()

    def to_dict(self):
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
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
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name or self.username,
            'avatar_url': self.avatar_url,
            'address': self.address,
            'interests': self.interests if self.interests else []
        }


class UserToken(models.Model):
    """Model to track user tokens for logout functionality."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens')
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