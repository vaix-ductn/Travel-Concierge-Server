"""Authentication serializers for request/response data handling."""

import re
from rest_framework import serializers
from django.core.validators import EmailValidator
from ..models import User
from base.serializers.base import BaseSerializer


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login request data.

    Validates username and password for authentication.
    Supports login by username or email.
    """

    username = serializers.CharField(
        min_length=3,
        max_length=50,
        required=True,
        help_text="Username or email (3-50 characters)"
    )
    password = serializers.CharField(
        min_length=6,
        max_length=255,
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Password (minimum 6 characters)"
    )

    def validate_username(self, value):
        """
        Validate username/email format.

        Args:
            value (str): Username or email input

        Returns:
            str: Cleaned and normalized username/email
        """
        if not value:
            raise serializers.ValidationError("Username or email is required")

        value = value.strip().lower()

        # Check if it's an email format
        if '@' in value:
            try:
                EmailValidator()(value)
                return value
            except serializers.ValidationError:
                raise serializers.ValidationError("Invalid email format")

        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username can only contain alphanumeric characters and underscores"
            )

        return value

    def validate_password(self, value):
        """
        Validate password requirements.

        Args:
            value (str): Password input

        Returns:
            str: Validated password
        """
        if not value:
            raise serializers.ValidationError("Password is required")

        if len(value.strip()) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")

        return value

    def validate(self, attrs):
        """
        Cross-field validation for login data.

        Args:
            attrs (dict): Validation data

        Returns:
            dict: Validated data
        """
        username = attrs.get('username', '').strip()
        password = attrs.get('password', '').strip()

        if not username:
            raise serializers.ValidationError("Username or email is required")

        if not password:
            raise serializers.ValidationError("Password is required")

        return attrs


class UserSerializer(BaseSerializer):
    """
    Serializer for user data in API responses.

    Provides consistent user data representation across the API.
    """

    user_uuid = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            'user_uuid', 'username', 'email', 'full_name',
            'avatar_url', 'address', 'interests',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['user_uuid', 'username', 'email', 'created_at', 'updated_at', 'last_login']

    def to_representation(self, instance):
        """
        Customize user data representation.

        Args:
            instance (User): User model instance

        Returns:
            dict: Serialized user data
        """
        data = super().to_representation(instance)

        # Ensure interests is always a list
        if not data.get('interests'):
            data['interests'] = []

        # Provide display name
        data['display_name'] = instance.display_name

        # Format timestamps
        for field in ['created_at', 'updated_at', 'last_login']:
            if data.get(field):
                data[field] = instance.__dict__[field].isoformat()

        return data


class TokenVerifySerializer(serializers.Serializer):
    """
    Serializer for token verification response.

    Used to return token validation results with user context.
    """

    success = serializers.BooleanField(
        default=True,
        help_text="Whether token verification was successful"
    )
    message = serializers.CharField(
        default="Token is valid",
        help_text="Human-readable verification message"
    )
    user = serializers.DictField(
        read_only=True,
        help_text="User data associated with the token"
    )
    token_expires_at = serializers.DateTimeField(
        required=False,
        help_text="Token expiration timestamp"
    )


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response data.

    Returns authentication token and user context after successful login.
    """

    success = serializers.BooleanField(
        default=True,
        help_text="Whether login was successful"
    )
    message = serializers.CharField(
        default="Login successful",
        help_text="Human-readable login message"
    )
    token = serializers.CharField(
        help_text="JWT authentication token"
    )
    user = serializers.DictField(
        help_text="User authentication context"
    )
    expires_at = serializers.DateTimeField(
        required=False,
        help_text="Token expiration timestamp"
    )


class LogoutResponseSerializer(serializers.Serializer):
    """
    Serializer for logout response data.

    Confirms successful logout and token invalidation.
    """

    success = serializers.BooleanField(
        default=True,
        help_text="Whether logout was successful"
    )
    message = serializers.CharField(
        default="Logout successful",
        help_text="Human-readable logout message"
    )


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for standardized error responses.

    Provides consistent error formatting across the API.
    """

    success = serializers.BooleanField(
        default=False,
        help_text="Always false for error responses"
    )
    message = serializers.CharField(
        help_text="Human-readable error message"
    )
    error_code = serializers.CharField(
        required=False,
        help_text="Machine-readable error code"
    )
    details = serializers.DictField(
        required=False,
        help_text="Additional error context and details"
    )
    timestamp = serializers.DateTimeField(
        required=False,
        help_text="Error occurrence timestamp"
    )