from rest_framework.request import Request
from .base import BasePermission

class ViewSetPermission(BasePermission):
    def get_view_method(self, request: Request, view) -> str:
        action = getattr(view, 'action', None)
        action = action if action is not None else str.lower(request.method)
        return action