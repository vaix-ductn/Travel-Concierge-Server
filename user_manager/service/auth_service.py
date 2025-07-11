"""Authentication service classes for business logic handling."""

import jwt
import hashlib
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers
from base.service.base_service import AbstractBaseService
from ..models import User, UserToken
from ..models.user_profile import UserProfile
from ..validation import AuthValidation, RateLimitValidation, TokenValidation, SecurityValidation


logger = logging.getLogger(__name__)


class TokenService(AbstractBaseService):
    """
    Service for JWT token management.

    Handles token generation, verification, and invalidation
    with proper database tracking for logout functionality.
    """

    # JWT Configuration
    JWT_SECRET = getattr(settings, 'JWT_SECRET', 'your-super-secret-jwt-key-here')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = getattr(settings, 'JWT_EXPIRATION_HOURS', 24)

    def _set_model(self) -> list:
        """Set the model for the base service."""
        return ['user_manager', 'UserToken']

    @classmethod
    def generate_token(cls, user):
        """
        Generate JWT token for user with database tracking.

        Args:
            user (User): User instance to generate token for

        Returns:
            str: Generated JWT token

        Raises:
            Exception: If token generation fails
        """
        try:
            # Create token payload
            payload = {
                'user_uuid': str(user.user_uuid),
                'username': user.username,
                'email': user.email,
                'iat': timezone.now(),
                'exp': timezone.now() + timedelta(hours=cls.JWT_EXPIRATION_HOURS)
            }

            # Generate JWT token
            token = jwt.encode(payload, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)

            # Store token in database for tracking
            cls._store_token(user, token)

            logger.info(f"Token generated successfully for user: {user.username}")
            return token

        except Exception as e:
            logger.error(f"Failed to generate token for user {user.username}: {str(e)}")
            raise Exception("Token generation failed")

    @classmethod
    def verify_token(cls, token):
        """
        Verify JWT token and return user data.

        Args:
            token (str): JWT token to verify

        Returns:
            tuple: (User instance, token payload)

        Raises:
            serializers.ValidationError: If token is invalid
        """
        try:
            # Validate token format
            TokenValidation.validate_token_format(token)

            # Check if token is blacklisted
            if cls._is_token_blacklisted(token):
                logger.warning(f"Attempt to use blacklisted token")
                raise serializers.ValidationError("Token has been invalidated")

            # Decode and verify token
            payload = jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])

            # Get user from payload
            user_uuid = payload.get('user_uuid')
            if not user_uuid:
                raise serializers.ValidationError("Invalid token payload")

            user = User.objects.get(user_uuid=user_uuid)

            logger.debug(f"Token verified successfully for user: {user.username}")
            return user, payload

        except jwt.ExpiredSignatureError:
            logger.warning("Expired token verification attempt")
            raise serializers.ValidationError("Token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid token verification attempt")
            raise serializers.ValidationError("Invalid token")
        except ObjectDoesNotExist:
            logger.error(f"Token verification failed - user not found for UUID: {user_uuid}")
            raise serializers.ValidationError("User not found")
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            raise serializers.ValidationError("Token verification failed")

    @classmethod
    def invalidate_token(cls, token):
        """
        Invalidate a specific token (for logout).

        Args:
            token (str): JWT token to invalidate

        Returns:
            bool: True if token was invalidated, False if not found
        """
        try:
            token_hash = TokenValidation.get_token_hash(token)

            with transaction.atomic():
                user_token = UserToken.objects.select_for_update().get(
                    token_hash=token_hash,
                    is_active=True
                )
                user_token.invalidate()

            logger.info(f"Token invalidated successfully for user: {user_token.user.username}")
            return True

        except ObjectDoesNotExist:
            logger.warning("Attempt to invalidate non-existent or inactive token")
            return False
        except Exception as e:
            logger.error(f"Failed to invalidate token: {str(e)}")
            return False

    @classmethod
    def invalidate_all_user_tokens(cls, user):
        """
        Invalidate all active tokens for a user.

        Args:
            user (User): User instance to invalidate tokens for

        Returns:
            int: Number of tokens invalidated
        """
        try:
            with transaction.atomic():
                count = user.tokens.filter(is_active=True).update(is_active=False)

            logger.info(f"Invalidated {count} tokens for user: {user.username}")
            return count

        except Exception as e:
            logger.error(f"Failed to invalidate all tokens for user {user.username}: {str(e)}")
            return 0

    @classmethod
    def _store_token(cls, user, token):
        """
        Store token hash in database for logout functionality.

        Args:
            user (User): User instance
            token (str): JWT token to store
        """
        try:
            token_hash = TokenValidation.get_token_hash(token)
            expires_at = timezone.now() + timedelta(hours=cls.JWT_EXPIRATION_HOURS)

            UserToken.create_token(
                user=user,
                token_hash=token_hash,
                expires_in_hours=cls.JWT_EXPIRATION_HOURS
            )

            logger.debug(f"Token stored in database for user: {user.username}")

        except Exception as e:
            logger.error(f"Failed to store token for user {user.username}: {str(e)}")
            # Don't raise exception here to not break token generation
            # The token will still work, just won't be tracked for logout

    @classmethod
    def _is_token_blacklisted(cls, token):
        """
        Check if token is blacklisted (invalidated).

        Args:
            token (str): JWT token to check

        Returns:
            bool: True if token is blacklisted, False otherwise
        """
        try:
            token_hash = TokenValidation.get_token_hash(token)
            user_token = UserToken.objects.get(token_hash=token_hash)
            return not user_token.is_valid()

        except ObjectDoesNotExist:
            # Token not found in database, consider it valid
            # This handles tokens created before the blacklist system
            return False
        except Exception as e:
            logger.error(f"Error checking token blacklist status: {str(e)}")
            return False

    @classmethod
    def cleanup_expired_tokens(cls):
        """
        Clean up expired tokens from database.

        Returns:
            int: Number of tokens cleaned up
        """
        try:
            count = UserToken.cleanup_expired_tokens()
            logger.info(f"Cleaned up {count} expired tokens")
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {str(e)}")
            return 0


class AuthService:
    """
    Service for authentication business logic.

    Handles user login, token verification, logout, and user creation
    with comprehensive error handling and security features.
    """

    @staticmethod
    def login_user(username_or_email, password, ip_address):
        """
        Authenticate user and return token with user data.

        Args:
            username_or_email (str): Username or email for login
            password (str): User password
            ip_address (str): Client IP address for rate limiting

        Returns:
            dict: Authentication result with token and user data
        """
        try:
            # Validate input
            username_or_email = AuthValidation.validate_username_format(username_or_email)
            password = AuthValidation.validate_password_strength(password)

            # Check rate limiting
            RateLimitValidation.check_login_rate_limit(ip_address)

            # Get user (support login by username or email)
            user = AuthService._get_user_by_credential(username_or_email)

            # Validate user exists and password
            SecurityValidation.validate_user_exists(user)
            SecurityValidation.validate_password_match(user, password)

            # Get user profile if available
            user_profile_uuid = AuthService._get_user_profile_uuid(user)

            # Login successful - update user state
            with transaction.atomic():
                user.update_last_login()
                RateLimitValidation.record_login_attempt(ip_address, success=True)

            # Generate token
            token = TokenService.generate_token(user)

            # Prepare user context
            user_context = user.get_auth_context()
            user_context['user_profile_uuid'] = user_profile_uuid

            logger.info(f"Successful login for user: {user.username} from IP: {ip_address}")

            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user_context,
                'expires_at': (timezone.now() + timedelta(hours=TokenService.JWT_EXPIRATION_HOURS)).isoformat()
            }

        except serializers.ValidationError as e:
            # Handle authentication failure
            RateLimitValidation.record_login_attempt(ip_address, success=False)

            error_code = getattr(e, 'code', None)
            error_message = str(e)

            logger.warning(f"Login failed for {username_or_email} from IP {ip_address}: {error_message}")

            if error_code == 'RATE_LIMIT_EXCEEDED':
                return {
                    'success': False,
                    'message': error_message,
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid username or password',
                    'error_code': 'INVALID_CREDENTIALS'
                }

        except Exception as e:
            logger.error(f"Unexpected error during login for {username_or_email}: {str(e)}")
            return {
                'success': False,
                'message': 'An error occurred during login',
                'error_code': 'INTERNAL_ERROR'
            }

    @staticmethod
    def verify_token(auth_header, ip_address):
        """
        Verify authentication token and return user data.

        Args:
            auth_header (str): Authorization header with Bearer token
            ip_address (str): Client IP address for rate limiting

        Returns:
            dict: Token verification result with user data
        """
        try:
            # Check rate limiting
            RateLimitValidation.check_token_verify_rate_limit(ip_address)
            RateLimitValidation.record_token_verify_request(ip_address)

            # Extract and validate token
            token = TokenValidation.validate_bearer_token(auth_header)

            # Verify token and get user
            user, payload = TokenService.verify_token(token)

            logger.debug(f"Token verified successfully for user: {user.username}")

            return {
                'success': True,
                'message': 'Token is valid',
                'user': user.get_auth_context(),
                'token_expires_at': datetime.fromtimestamp(payload.get('exp')).isoformat()
            }

        except serializers.ValidationError as e:
            error_code = getattr(e, 'code', None)
            error_message = str(e)

            logger.warning(f"Token verification failed from IP {ip_address}: {error_message}")

            if error_code == 'RATE_LIMIT_EXCEEDED':
                return {
                    'success': False,
                    'message': error_message,
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid or expired token',
                    'error_code': 'INVALID_TOKEN'
                }

        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            return {
                'success': False,
                'message': 'Token verification failed',
                'error_code': 'INTERNAL_ERROR'
            }

    @staticmethod
    def logout_user(auth_header):
        """
        Logout user by invalidating token.

        Args:
            auth_header (str): Authorization header with Bearer token

        Returns:
            dict: Logout result
        """
        try:
            # Extract and validate token
            token = TokenValidation.validate_bearer_token(auth_header)

            # Verify token first to ensure it's valid
            user, payload = TokenService.verify_token(token)

            # Invalidate the token
            TokenService.invalidate_token(token)

            logger.info(f"Successful logout for user: {user.username}")

            return {
                'success': True,
                'message': 'Logout successful'
            }

        except serializers.ValidationError as e:
            logger.warning(f"Logout failed with invalid token: {str(e)}")
            return {
                'success': False,
                'message': 'Invalid or expired token',
                'error_code': 'INVALID_TOKEN'
            }

        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            return {
                'success': False,
                'message': 'Logout failed',
                'error_code': 'INTERNAL_ERROR'
            }

    @staticmethod
    def create_user(username, email, password, **kwargs):
        """
        Create a new user with validation.

        Args:
            username (str): Unique username
            email (str): User email address
            password (str): User password
            **kwargs: Additional user data

        Returns:
            User: Created user instance

        Raises:
            serializers.ValidationError: If validation fails
        """
        try:
            # Validate input
            username = AuthValidation.validate_username_format(username)
            email = AuthValidation.validate_email_format(email)
            password = AuthValidation.validate_password_strength(password)

            # Check uniqueness
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError("Username already exists")

            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("Email already exists")

            # Create user
            with transaction.atomic():
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

            logger.info(f"User created successfully: {username}")
            return user

        except Exception as e:
            logger.error(f"Failed to create user {username}: {str(e)}")
            raise

    @staticmethod
    def get_client_ip(request):
        """
        Extract client IP address from request.

        Args:
            request: Django request object

        Returns:
            str: Client IP address
        """
        # Check for forwarded IP (proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in case of multiple proxies
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')

        return ip

    @staticmethod
    def _get_user_by_credential(username_or_email):
        """
        Get user by username or email.

        Args:
            username_or_email (str): Username or email

        Returns:
            User or None: User instance if found
        """
        try:
            if '@' in username_or_email:
                # Login by email
                return User.objects.get(email=username_or_email)
            else:
                # Login by username
                return User.objects.get(username=username_or_email)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def _get_user_profile_uuid(user):
        """
        Get user profile UUID if available.

        Args:
            user (User): User instance

        Returns:
            str or None: User profile UUID
        """
        try:
            user_profile = UserProfile.objects.get(user_uuid=user.user_uuid)
            return str(user_profile.user_profile_uuid)
        except (UserProfile.DoesNotExist, AttributeError):
            return None