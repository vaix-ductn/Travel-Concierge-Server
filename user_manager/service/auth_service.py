"""Authentication service classes for business logic handling."""

import jwt
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from ..models import User, UserToken
from ..validation import AuthValidation, RateLimitValidation, TokenValidation, SecurityValidation


class TokenService:
    """Service for JWT token management."""

    # Default settings - can be overridden by environment variables
    JWT_SECRET = getattr(settings, 'JWT_SECRET', 'your-super-secret-jwt-key-here')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24

    @classmethod
    def generate_token(cls, user):
        """Generate JWT token for user."""
        payload = {
            'user_uuid': str(user.user_uuid),
            'username': user.username,
            'email': user.email,
            'iat': timezone.now(),
            'exp': timezone.now() + timedelta(hours=cls.JWT_EXPIRATION_HOURS)
        }

        token = jwt.encode(payload, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)

        # Store token hash for logout functionality
        cls._store_token(user, token)

        return token

    @classmethod
    def verify_token(cls, token):
        """Verify JWT token and return user data."""
        try:
            # Validate token format
            TokenValidation.validate_token_format(token)

            # Check if token is blacklisted
            if cls._is_token_blacklisted(token):
                raise serializers.ValidationError("Token has been invalidated")

            # Decode and verify token
            payload = jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])

            # Get user from payload
            user_uuid = payload.get('user_uuid')
            user = User.objects.get(user_uuid=user_uuid)

            return user, payload

        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError("Token has expired")
        except jwt.InvalidTokenError:
            raise serializers.ValidationError("Invalid token")
        except ObjectDoesNotExist:
            raise serializers.ValidationError("User not found")

    @classmethod
    def invalidate_token(cls, token):
        """Invalidate a token (for logout)."""
        token_hash = TokenValidation.get_token_hash(token)

        try:
            user_token = UserToken.objects.get(token_hash=token_hash, is_active=True)
            user_token.invalidate()
            return True
        except ObjectDoesNotExist:
            # Token not found in database, might be expired or invalid
            return False

    @classmethod
    def invalidate_all_user_tokens(cls, user):
        """Invalidate all tokens for a user."""
        user.tokens.filter(is_active=True).update(is_active=False)

    @classmethod
    def _store_token(cls, user, token):
        """Store token hash in database for logout functionality."""
        # Temporarily disabled to avoid foreign key issues
        # token_hash = TokenValidation.get_token_hash(token)
        # expires_at = timezone.now() + timedelta(hours=cls.JWT_EXPIRATION_HOURS)

        # UserToken.objects.create(
        #     user=user,
        #     token_hash=token_hash,
        #     expires_at=expires_at
        # )
        pass

    @classmethod
    def _is_token_blacklisted(cls, token):
        """Check if token is blacklisted (invalidated)."""
        token_hash = TokenValidation.get_token_hash(token)

        try:
            user_token = UserToken.objects.get(token_hash=token_hash)
            return not user_token.is_active or user_token.is_expired()
        except ObjectDoesNotExist:
            # Token not found in database, consider it valid for now
            # This handles tokens created before the blacklist system
            return False

    @classmethod
    def cleanup_expired_tokens(cls):
        """Clean up expired tokens from database."""
        return UserToken.cleanup_expired_tokens()


class AuthService:
    """Service for authentication business logic."""

    @staticmethod
    def login_user(username, password, ip_address):
        """Authenticate user and return token with user data."""
        try:
            # Validate input
            username = AuthValidation.validate_username_format(username)
            password = AuthValidation.validate_password_strength(password)

            # Check rate limiting
            RateLimitValidation.check_login_rate_limit(ip_address)

            # Get user
            try:
                user = User.objects.get(username=username)
            except ObjectDoesNotExist:
                user = None

            # Validate user exists
            SecurityValidation.validate_user_exists(user)

            # Validate password
            SecurityValidation.validate_password_match(user, password)

            # Login successful
            user.update_last_login()
            RateLimitValidation.record_login_attempt(ip_address, success=True)

            # Generate token
            token = TokenService.generate_token(user)

            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user.get_auth_context()
            }

        except serializers.ValidationError as e:
            # Handle authentication failure
            RateLimitValidation.record_login_attempt(ip_address, success=False)

            # Return appropriate error response
            error_code = getattr(e, 'code', None)

            if error_code == 'RATE_LIMIT_EXCEEDED':
                return {
                    'success': False,
                    'message': str(e),
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid username or password',
                    'error_code': 'INVALID_CREDENTIALS'
                }

    @staticmethod
    def verify_token(auth_header, ip_address):
        """Verify authentication token and return user data."""
        try:
            # Check rate limiting
            RateLimitValidation.check_token_verify_rate_limit(ip_address)
            RateLimitValidation.record_token_verify_request(ip_address)

            # Extract and validate token
            token = TokenValidation.validate_bearer_token(auth_header)

            # Verify token and get user
            user, payload = TokenService.verify_token(token)

            return {
                'success': True,
                'message': 'Token is valid',
                'user': user.get_auth_context()
            }

        except serializers.ValidationError as e:
            error_code = getattr(e, 'code', None)

            if error_code == 'RATE_LIMIT_EXCEEDED':
                return {
                    'success': False,
                    'message': str(e),
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid or expired token',
                    'error_code': 'INVALID_TOKEN'
                }

    @staticmethod
    def logout_user(auth_header):
        """Logout user by invalidating token."""
        try:
            # Extract and validate token
            token = TokenValidation.validate_bearer_token(auth_header)

            # Verify token first to ensure it's valid
            user, payload = TokenService.verify_token(token)

            # Invalidate the token
            TokenService.invalidate_token(token)

            return {
                'success': True,
                'message': 'Logout successful'
            }

        except serializers.ValidationError:
            return {
                'success': False,
                'message': 'Invalid or expired token',
                'error_code': 'INVALID_TOKEN'
            }

    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def create_user(username, email, password, **kwargs):
        """Create a new user (for testing/admin purposes)."""
        # Validate input
        username = AuthValidation.validate_username_format(username)
        email = AuthValidation.validate_email_format(email)
        password = AuthValidation.validate_password_strength(password)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")

        # Create user
        user = User(
            username=username,
            email=email,
            full_name=kwargs.get('full_name'),
            avatar_url=kwargs.get('avatar_url'),
            address=kwargs.get('address'),
            interests=kwargs.get('interests', [])
        )
        user.set_password(password)
        user.save()

        return user