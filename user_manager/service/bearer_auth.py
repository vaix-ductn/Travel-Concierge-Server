import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .auth_service import TokenService

class BearerHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        logger = logging.getLogger("user_manager.auth")
        token = request.META.get('HTTP_BEARER')
        if not token:
            auth = request.META.get('HTTP_AUTHORIZATION')
            if auth and auth.lower().startswith('bearer '):
                token = auth[7:].strip()
        if not token:
            logger.warning(f"No token found in request headers for path: {request.path}")
            return None
        logger.info(f"Received token for path {request.path}: {token[:20]}... (truncated)")
        try:
            user, payload = TokenService.verify_token(token)
            logger.info(f"Token valid for user: {getattr(user, 'username', None)} | path: {request.path}")
            return (user, None)
        except Exception as e:
            logger.error(f"Token invalid or expired for path {request.path}: {token[:20]}... | Error: {e}")
            raise exceptions.AuthenticationFailed('Invalid or expired token')