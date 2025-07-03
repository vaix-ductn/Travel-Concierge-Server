"""Authentication API views for handling HTTP requests."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..service import AuthService
from ..serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    TokenVerifySerializer,
    LogoutResponseSerializer,
    ErrorResponseSerializer
)


class LoginView(APIView):
    """API view for user login."""

    @swagger_auto_schema(
        operation_summary="Login User",
        operation_description="Authenticates user credentials and returns authentication token and user data.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=LoginResponseSerializer,
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Login successful",
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": "user_12345",
                            "username": "alan_love",
                            "email": "alanlovelq@gmail.com",
                            "full_name": "Alan Love",
                            "avatar_url": "https://example.com/avatars/alan_love.jpg",
                            "address": "Ha Noi, Viet Nam",
                            "interests": ["Travel", "Photography", "Food"]
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=ErrorResponseSerializer,
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Username and password are required"
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=ErrorResponseSerializer,
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Invalid username or password"
                    }
                }
            ),
            429: openapi.Response(
                description="Too Many Requests",
                schema=ErrorResponseSerializer,
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Too many login attempts. Please try again later."
                    }
                }
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        """Handle login request."""
        # Validate request data
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Invalid input data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get validated data
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Get client IP
        ip_address = AuthService.get_client_ip(request)

        # Attempt login
        result = AuthService.login_user(username, password, ip_address)

        # Return appropriate response
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            error_code = result.get('error_code')
            if error_code == 'RATE_LIMIT_EXCEEDED':
                return Response(result, status=status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                return Response(result, status=status.HTTP_401_UNAUTHORIZED)


class VerifyTokenView(APIView):
    """API view for token verification."""

    @swagger_auto_schema(
        operation_summary="Verify Token",
        operation_description="Verifies if the provided authentication token is valid and returns user information.",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer token",
                type=openapi.TYPE_STRING,
                required=True,
                format="Bearer <token>"
            )
        ],
        responses={
            200: openapi.Response(
                description="Token is valid",
                schema=TokenVerifySerializer,
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Token is valid",
                        "user": {
                            "id": "user_12345",
                            "username": "alan_love",
                            "email": "alanlovelq@gmail.com",
                            "full_name": "Alan Love",
                            "avatar_url": "https://example.com/avatars/alan_love.jpg",
                            "address": "Ha Noi, Viet Nam",
                            "interests": ["Travel", "Photography", "Food"]
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=ErrorResponseSerializer,
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Invalid or expired token"
                    }
                }
            ),
            429: openapi.Response(
                description="Too Many Requests",
                schema=ErrorResponseSerializer,
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Too many requests. Please try again later."
                    }
                }
            )
        },
        tags=['Authentication']
    )
    def get(self, request):
        """Handle token verification request."""
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header:
            return Response(
                {
                    'success': False,
                    'message': 'Authorization header is required'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get client IP
        ip_address = AuthService.get_client_ip(request)

        # Verify token
        result = AuthService.verify_token(auth_header, ip_address)

        # Return appropriate response
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            error_code = result.get('error_code')
            if error_code == 'RATE_LIMIT_EXCEEDED':
                return Response(result, status=status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                return Response(result, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """API view for user logout."""

    @swagger_auto_schema(
        operation_summary="Logout User",
        operation_description="Invalidates the user's authentication token and logs them out.",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer token",
                type=openapi.TYPE_STRING,
                required=True,
                format="Bearer <token>"
            )
        ],
        responses={
            200: openapi.Response(
                description="Logout successful",
                schema=LogoutResponseSerializer,
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Logout successful"
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=ErrorResponseSerializer,
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Invalid or expired token"
                    }
                }
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        """Handle logout request."""
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header:
            return Response(
                {
                    'success': False,
                    'message': 'Authorization header is required'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Logout user
        result = AuthService.logout_user(auth_header)

        # Return appropriate response
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_401_UNAUTHORIZED)