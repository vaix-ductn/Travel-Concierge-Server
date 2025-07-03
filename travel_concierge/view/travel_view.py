"""
View layer for travel-related endpoints
This handles HTTP requests and delegates to service layer
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
import logging

from ..service.travel_service import TravelService
from ..validation.travel_validation import (
    TravelRecommendationValidation,
    ToolsStatusValidation
)


class TravelView:
    """View class for travel-related API endpoints"""

    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def get_travel_recommendations(request):
        """
        Get travel recommendations based on user preferences

        Expected payload:
        {
            "destination_type": "beach",
            "budget_range": "mid-range",
            "travel_dates": "Summer 2024",
            "group_size": 2,
            "interests": ["relaxation", "culture"],
            "special_requirements": "Accessible accommodations"
        }
        """
        try:
            # Validate request data
            validation = TravelRecommendationValidation(data=request.data)
            validation.is_valid(raise_exception=True)

            # Process travel recommendation
            travel_service = TravelService()
            result = travel_service.process_travel_recommendation_request(validation.validated_data)

            return Response({
                'success': True,
                'data': result
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error in get_travel_recommendations: {e}")
            return Response({
                'success': False,
                'error': 'Unable to process travel recommendation request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def get_tools_status(request):
        """
        Get status of travel tools and integrations

        Query parameters:
        - tool_names: list of tool names to check (optional)
        - include_health_check: boolean (default: true)
        - detailed_status: boolean (default: false)
        """
        try:
            # Validate query parameters
            validation = ToolsStatusValidation(data=request.query_params)
            validation.is_valid(raise_exception=True)

            # Get tools status
            travel_service = TravelService()
            tools_status = travel_service.get_travel_tools_status()

            return Response({
                'success': True,
                'data': tools_status
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error in get_tools_status: {e}")
            return Response({
                'success': False,
                'error': 'Unable to get tools status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def health_check(request):
        """
        Simple health check endpoint for the travel concierge system
        """
        try:
            # Basic health check
            travel_service = TravelService()
            tools_status = travel_service.get_travel_tools_status()

            overall_healthy = tools_status.get('overall_status') == 'healthy'

            return Response({
                'success': True,
                'status': 'healthy' if overall_healthy else 'degraded',
                'timestamp': None,  # Can add timestamp if needed
                'services': {
                    'travel_service': 'operational',
                    'tools': tools_status.get('overall_status', 'unknown')
                }
            })

        except Exception as e:
            logging.getLogger(__name__).error(f"Error in health_check: {e}")
            return Response({
                'success': False,
                'status': 'unhealthy',
                'error': 'Health check failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function-based views for URL routing
def get_travel_recommendations(request):
    """Function wrapper for get travel recommendations"""
    return TravelView.get_travel_recommendations(request)

def get_tools_status(request):
    """Function wrapper for get tools status"""
    return TravelView.get_tools_status(request)

def health_check(request):
    """Function wrapper for health check"""
    return TravelView.health_check(request)