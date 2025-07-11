"""Authentication API views for handling HTTP requests."""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from base.response.utils import api_response_success, api_response_error
from ..service import AuthService
from ..serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    TokenVerifySerializer,
    LogoutResponseSerializer,
    ErrorResponseSerializer
)
from ..permission.auth_permission import AuthPermission


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    API view for user authentication.

    Handles user login with username/email and password.
    Supports rate limiting and comprehensive error handling.
    """

    permission_classes = [AuthPermission]
    serializer_class = LoginSerializer

    def post(self, request):
        """
        Authenticate user and return JWT token.

        Expected payload:
        {
            "username": "user@example.com",  // username or email
            "password": "userpassword"
        }

        Returns:
        {
            "success": true,
            "message": "Login successful",
            "token": "jwt_token_here",
            "user": {
                "user_uuid": "uuid",
                "username": "username",
                "email": "email",
                "full_name": "Full Name",
                "user_profile_uuid": "profile_uuid"
            },
            "expires_at": "2024-01-01T00:00:00Z"
        }
        """
        try:
            # Log login attempt
            client_ip = AuthService.get_client_ip(request)
            logger.info(f"Login attempt from IP: {client_ip}")

            # Validate request data
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Login validation failed from IP {client_ip}: {serializer.errors}")
                return api_response_error(
                    msg='Invalid input data',
                    data={'validation_errors': serializer.errors},
                    http_code=status.HTTP_400_BAD_REQUEST
                )

            # Get validated credentials
            username_or_email = serializer.validated_data['username']
            password = serializer.validated_data['password']

            # Attempt authentication
            result = AuthService.login_user(username_or_email, password, client_ip)

            # Handle response based on result
            if result['success']:
                logger.info(f"Successful login for user: {username_or_email} from IP: {client_ip}")
                return api_response_success(
                    data={
                        'token': result.get('token'),
                        'user': result.get('user'),
                        'expires_at': result.get('expires_at')
                    },
                    msg=result.get('message', 'Login successful'),
                    http_code=status.HTTP_200_OK
                )
            else:
                error_code = result.get('error_code')
                error_message = result.get('message', 'Authentication failed')

                logger.warning(f"Login failed for {username_or_email} from IP {client_ip}: {error_code}")

                # Determine appropriate HTTP status code
                if error_code == 'RATE_LIMIT_EXCEEDED':
                    status_code = status.HTTP_429_TOO_MANY_REQUESTS
                elif error_code == 'INVALID_CREDENTIALS':
                    status_code = status.HTTP_401_UNAUTHORIZED
                else:
                    status_code = status.HTTP_400_BAD_REQUEST

                return api_response_error(
                    msg=error_message,
                    data={'error_code': error_code},
                    http_code=status_code
                )

        except Exception as e:
            logger.error(f"Unexpected error during login from IP {client_ip}: {str(e)}")
            return api_response_error(
                msg='An internal error occurred',
                data={'error_code': 'INTERNAL_ERROR'},
                http_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get login form information (for API documentation).

        Returns available login methods and requirements.
        """
        return api_response_success(
            msg='Login endpoint information',
            data={
                'method': 'POST',
                'content_type': 'application/json',
                'required_fields': ['username', 'password'],
                'optional_fields': [],
                'login_methods': ['username', 'email'],
                'rate_limiting': 'Enabled',
                'description': 'Authenticate with username/email and password to receive JWT token'
            }
        )


class VerifyTokenView(APIView):
    """
    API view for JWT token verification.

    Validates authentication tokens and returns user information.
    Used for protected route access validation.
    """

    permission_classes = [AuthPermission]
    serializer_class = TokenVerifySerializer

    def get(self, request):
        """
        Verify JWT token and return user data.

        Headers:
        Authorization: Bearer <jwt_token>

        Returns:
        {
            "success": true,
            "message": "Token is valid",
            "user": {
                "user_uuid": "uuid",
                "username": "username",
                "email": "email",
                "full_name": "Full Name"
            },
            "token_expires_at": "2024-01-01T00:00:00Z"
        }
        """
        try:
            # Get client information
            client_ip = AuthService.get_client_ip(request)
            auth_header = request.META.get('HTTP_AUTHORIZATION')

            logger.debug(f"Token verification request from IP: {client_ip}")

            # Validate authorization header
            if not auth_header:
                logger.warning(f"Token verification failed - missing auth header from IP: {client_ip}")
                return api_response_error(
                    msg='Authorization header is required',
                    data={'error_code': 'MISSING_AUTH_HEADER'},
                    http_code=status.HTTP_401_UNAUTHORIZED
                )

            # Verify token
            result = AuthService.verify_token(auth_header, client_ip)

            # Handle response
            if result['success']:
                logger.debug(f"Token verified successfully from IP: {client_ip}")
                return api_response_success(
                    data={
                        'user': result.get('user'),
                        'token_expires_at': result.get('token_expires_at')
                    },
                    msg=result.get('message', 'Token is valid'),
                    http_code=status.HTTP_200_OK
                )
            else:
                error_code = result.get('error_code')
                error_message = result.get('message', 'Token verification failed')

                logger.warning(f"Token verification failed from IP {client_ip}: {error_code}")

                # Determine appropriate status code
                if error_code == 'RATE_LIMIT_EXCEEDED':
                    status_code = status.HTTP_429_TOO_MANY_REQUESTS
                elif error_code == 'INVALID_TOKEN':
                    status_code = status.HTTP_401_UNAUTHORIZED
                else:
                    status_code = status.HTTP_400_BAD_REQUEST

                return api_response_error(
                    msg=error_message,
                    data={'error_code': error_code},
                    http_code=status_code
                )

        except Exception as e:
            logger.error(f"Unexpected error during token verification from IP {client_ip}: {str(e)}")
            return api_response_error(
                msg='Token verification failed',
                data={'error_code': 'INTERNAL_ERROR'},
                http_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    """
    API view for user logout.

    Invalidates the provided JWT token to prevent further use.
    Essential for secure session management.
    """

    permission_classes = [AuthPermission]
    serializer_class = LogoutResponseSerializer

    def post(self, request):
        """
        Logout user by invalidating JWT token.

        Headers:
        Authorization: Bearer <jwt_token>

        Returns:
        {
            "success": true,
            "message": "Logout successful"
        }
        """
        try:
            # Get client information
            client_ip = AuthService.get_client_ip(request)
            auth_header = request.META.get('HTTP_AUTHORIZATION')

            logger.info(f"Logout request from IP: {client_ip}")

            # Validate authorization header
            if not auth_header:
                logger.warning(f"Logout failed - missing auth header from IP: {client_ip}")
                return api_response_error(
                    msg='Authorization header is required',
                    data={'error_code': 'MISSING_AUTH_HEADER'},
                    http_code=status.HTTP_401_UNAUTHORIZED
                )

            # Perform logout
            result = AuthService.logout_user(auth_header)

            # Handle response
            if result['success']:
                logger.info(f"Successful logout from IP: {client_ip}")
                return api_response_success(
                    data=None,
                    msg=result.get('message', 'Logout successful'),
                    http_code=status.HTTP_200_OK
                )
            else:
                error_code = result.get('error_code')
                error_message = result.get('message', 'Logout failed')

                logger.warning(f"Logout failed from IP {client_ip}: {error_code}")

                # Determine appropriate status code
                if error_code == 'INVALID_TOKEN':
                    status_code = status.HTTP_401_UNAUTHORIZED
                else:
                    status_code = status.HTTP_400_BAD_REQUEST

                return api_response_error(
                    msg=error_message,
                    data={'error_code': error_code},
                    http_code=status_code
                )

        except Exception as e:
            logger.error(f"Unexpected error during logout from IP {client_ip}: {str(e)}")
            return api_response_error(
                msg='Logout failed',
                data={'error_code': 'INTERNAL_ERROR'},
                http_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get logout endpoint information (for API documentation).

        Returns logout method requirements.
        """
        return api_response_success(
            msg='Logout endpoint information',
            data={
                'method': 'POST',
                'content_type': 'application/json',
                'required_headers': ['Authorization: Bearer <token>'],
                'description': 'Invalidate JWT token to logout user securely'
            }
        )