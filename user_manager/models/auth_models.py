"""Authentication models for user management and token handling."""

import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.core.exceptions import ValidationError


class User(models.Model):
    """
    User model for authentication system.

    This model handles user authentication, profile information,
    and provides context for AI agent interactions.
    """

    # Primary fields
    user_uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the user"
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique username for login"
    )
    email = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="User's email address"
    )
    password_hash = models.CharField(
        max_length=255,
        help_text="Hashed password"
    )

    # Profile fields
    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="User's full display name"
    )
    avatar_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL to user's avatar image"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="User's address"
    )
    interests = models.JSONField(
        default=list,
        blank=True,
        help_text="List of user interests"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Account creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last login timestamp"
    )

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.email})"

    def clean(self):
        """Validate model fields."""
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()
        if self.username:
            self.username = self.username.strip()

    def save(self, *args, **kwargs):
        """Override save to perform validation."""
        self.clean()
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """
        Hash and set password.

        Args:
            raw_password (str): Plain text password to hash
        """
        if not raw_password:
            raise ValidationError("Password cannot be empty")
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Check if provided password matches stored hash.

        Args:
            raw_password (str): Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        if not raw_password or not self.password_hash:
            return False
        return check_password(raw_password, self.password_hash)

    def update_last_login(self):
        """Update last login timestamp efficiently."""
        User.objects.filter(user_uuid=self.user_uuid).update(
            last_login=timezone.now()
        )

    def to_dict(self):
        """
        Convert user to dictionary for API responses.

        Returns:
            dict: User data suitable for API responses
        """
        return {
            'user_uuid': str(self.user_uuid),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'address': self.address,
            'interests': self.interests or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

    def get_auth_context(self):
        """
        Get user context for authentication responses.

        Returns:
            dict: Minimal user context for auth responses
        """
        return {
            'user_uuid': str(self.user_uuid),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name or self.username,
            'avatar_url': self.avatar_url,
        }

    @property
    def is_authenticated(self):
        """Always returns True for authenticated users."""
        return True

    @property
    def display_name(self):
        """Get the best available display name for the user."""
        return self.full_name or self.username


class UserToken(models.Model):
    """
    Model to track user tokens for authentication and logout functionality.

    This model ensures tokens can be properly invalidated during logout
    and provides cleanup for expired tokens.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tokens',
        to_field='user_uuid',
        help_text="User this token belongs to"
    )
    token_hash = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Hashed token value"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Token creation timestamp"
    )
    expires_at = models.DateTimeField(
        help_text="Token expiration timestamp"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether token is still valid"
    )

    class Meta:
        db_table = 'user_tokens'
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = "User Token"
        verbose_name_plural = "User Tokens"

    def __str__(self):
        status = "active" if self.is_active and not self.is_expired() else "inactive"
        return f"Token for {self.user.username} ({status})"

    def is_expired(self):
        """
        Check if token is expired.

        Returns:
            bool: True if token has expired, False otherwise
        """
        return timezone.now() > self.expires_at

    def is_valid(self):
        """
        Check if token is both active and not expired.

        Returns:
            bool: True if token is valid, False otherwise
        """
        return self.is_active and not self.is_expired()

    def invalidate(self):
        """Mark the token as inactive."""
        self.is_active = False
        self.save(update_fields=['is_active'])

    @classmethod
    def cleanup_expired_tokens(cls):
        """
        Clean up expired and inactive tokens.

        Returns:
            int: Number of tokens cleaned up
        """
        expired_tokens = cls.objects.filter(
            models.Q(expires_at__lt=timezone.now()) | models.Q(is_active=False)
        )
        count = expired_tokens.count()
        expired_tokens.delete()
        return count

    @classmethod
    def create_token(cls, user, token_hash, expires_in_hours=24):
        """
        Create a new token for a user.

        Args:
            user (User): User to create token for
            token_hash (str): Hashed token value
            expires_in_hours (int): Token expiration time in hours

        Returns:
            UserToken: Created token instance
        """
        expires_at = timezone.now() + timedelta(hours=expires_in_hours)
        return cls.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at
        )