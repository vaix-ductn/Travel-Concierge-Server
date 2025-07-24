"""
Custom middleware to bypass CSRF for agent endpoints
"""

from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware


class AgentCSRFBypassMiddleware(MiddlewareMixin):
    """
    Middleware to bypass CSRF for agent endpoints
    """

    def process_request(self, request):
        # Check if this is an agent endpoint
        if request.path.startswith('/api/agent/'):
            # Set a flag to bypass CSRF
            request._agent_endpoint = True
        return None


class CustomCsrfViewMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that bypasses agent endpoints
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Skip CSRF for agent endpoints
        if hasattr(request, '_agent_endpoint') and request._agent_endpoint:
            return None

        # Use parent CSRF logic for other endpoints
        return super().process_view(request, callback, callback_args, callback_kwargs)