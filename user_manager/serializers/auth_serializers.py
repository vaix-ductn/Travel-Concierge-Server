"""Authentication serializers for request/response data handling."""

from rest_framework import serializers
from ..models import User


class LoginSerializer(serializers.Serializer):
    """Serializer for login request data."""

    username = serializers.CharField(
        min_length=3,
        max_length=50,
        required=True,
        help_text="Username (3-50 characters, alphanumeric and underscore only)"
    )
    password = serializers.CharField(
        min_length=6,
        required=True,
        write_only=True,
        help_text="Password (minimum 6 characters)"
    )

    def validate_username(self, value):
        """Validate username format."""
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Username can only contain alphanumeric characters and underscores"
            )
        return value.lower()  # Normalize to lowercase

    def validate(self, attrs):
        """Additional validation for login data."""
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError("Username and password are required")

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data in API responses."""

    class Meta:
        model = User
        fields = ['user_uuid', 'username', 'email', 'full_name', 'avatar_url', 'address', 'interests']
        read_only_fields = ['user_uuid']

    def to_representation(self, instance):
        """Customize user data representation."""
        data = super().to_representation(instance)

        # Ensure interests is always a list
        if not data.get('interests'):
            data['interests'] = []

        # Provide default full_name if not set
        if not data.get('full_name'):
            data['full_name'] = data.get('username', '')

        return data


class TokenVerifySerializer(serializers.Serializer):
    """Serializer for token verification response."""

    success = serializers.BooleanField(default=True)
    message = serializers.CharField(default="Token is valid")
    user = UserSerializer(read_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response data."""

    success = serializers.BooleanField(default=True)
    message = serializers.CharField(default="Login successful")
    token = serializers.CharField(help_text="JWT authentication token")
    user = UserSerializer(read_only=True)


class LogoutResponseSerializer(serializers.Serializer):
    """Serializer for logout response data."""

    success = serializers.BooleanField(default=True)
    message = serializers.CharField(default="Logout successful")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error response data."""

    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    error_code = serializers.CharField(required=False)
    details = serializers.DictField(required=False)