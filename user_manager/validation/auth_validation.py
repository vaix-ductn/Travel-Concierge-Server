"""Authentication validation classes for business logic validation."""

import re
import hashlib
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers
from base.validation.base import Validation


class AuthValidation:
    """Validation class for authentication business logic."""

    @staticmethod
    def validate_username_format(username):
        """Validate username format according to spec."""
        if not username:
            raise serializers.ValidationError("Username is required")

        if len(username) < 3 or len(username) > 50:
            raise serializers.ValidationError("Username must be between 3 and 50 characters")

        # Only alphanumeric and underscore allowed
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise serializers.ValidationError(
                "Username can only contain alphanumeric characters and underscores"
            )

        return username.lower()

    @staticmethod
    def validate_password_strength(password):
        """Validate password strength according to spec."""
        if not password:
            raise serializers.ValidationError("Password is required")

        if len(password) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")

        return password

    @staticmethod
    def validate_email_format(email):
        """Validate email format."""
        if not email:
            raise serializers.ValidationError("Email is required")

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise serializers.ValidationError("Invalid email format")

        return email.lower()

    @staticmethod
    def sanitize_input(value):
        """Sanitize user input to prevent injection attacks."""
        if not value:
            return value

        # Basic sanitization - remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        sanitized = str(value)
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized.strip()


class RateLimitValidation:
    """Rate limiting validation for login attempts."""

    LOGIN_RATE_LIMIT_ATTEMPTS = 5
    LOGIN_RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
    TOKEN_VERIFY_RATE_LIMIT = 100  # requests per minute

    @classmethod
    def check_login_rate_limit(cls, ip_address):
        """Check if IP has exceeded login rate limit."""
        cache_key = f"login_attempts_{ip_address}"
        attempts = cache.get(cache_key, 0)

        if attempts >= cls.LOGIN_RATE_LIMIT_ATTEMPTS:
            raise serializers.ValidationError(
                "Too many login attempts. Please try again later.",
                code="RATE_LIMIT_EXCEEDED"
            )

        return True

    @classmethod
    def record_login_attempt(cls, ip_address, success=False):
        """Record a login attempt for rate limiting."""
        cache_key = f"login_attempts_{ip_address}"

        if success:
            # Clear attempts on successful login
            cache.delete(cache_key)
        else:
            # Increment failed attempts
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, cls.LOGIN_RATE_LIMIT_WINDOW)

    @classmethod
    def check_token_verify_rate_limit(cls, ip_address):
        """Check if IP has exceeded token verification rate limit."""
        cache_key = f"token_verify_{ip_address}"
        requests = cache.get(cache_key, 0)

        if requests >= cls.TOKEN_VERIFY_RATE_LIMIT:
            raise serializers.ValidationError(
                "Too many requests. Please try again later.",
                code="RATE_LIMIT_EXCEEDED"
            )

        return True

    @classmethod
    def record_token_verify_request(cls, ip_address):
        """Record a token verification request."""
        cache_key = f"token_verify_{ip_address}"
        requests = cache.get(cache_key, 0) + 1
        cache.set(cache_key, requests, 60)  # 1 minute window


class TokenValidation:
    """Token validation for JWT authentication."""

    @staticmethod
    def validate_token_format(token):
        """Validate JWT token format."""
        if not token:
            raise serializers.ValidationError("Token is required")

        # JWT should have 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            raise serializers.ValidationError("Invalid token format")

        return token

    @staticmethod
    def get_token_hash(token):
        """Get hash of token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def validate_bearer_token(auth_header):
        """Extract and validate Bearer token from Authorization header."""
        if not auth_header:
            raise serializers.ValidationError("Authorization header is required")

        if not auth_header.startswith('Bearer '):
            raise serializers.ValidationError("Invalid authorization header format")

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        return TokenValidation.validate_token_format(token)


class SecurityValidation:
    """Security validation for various authentication scenarios."""

    @staticmethod
    def validate_user_exists(user):
        """Validate that user exists and is active."""
        if not user:
            raise serializers.ValidationError(
                "Invalid username or password",
                code="INVALID_CREDENTIALS"
            )

        return True

    @staticmethod
    def validate_password_match(user, password):
        """Validate that password matches user's stored password."""
        if not user.check_password(password):
            raise serializers.ValidationError(
                "Invalid username or password",
                code="INVALID_CREDENTIALS"
            )

        return True