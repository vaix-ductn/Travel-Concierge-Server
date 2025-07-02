# NOTE: Profile views have been moved to user_manager app
# This file can contain other travel concierge views

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

# Add other travel concierge API views here
# Example:
# @api_view(['GET'])
# def get_travel_recommendations(request):
#     pass