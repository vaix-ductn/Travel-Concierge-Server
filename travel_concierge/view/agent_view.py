"""
View layer for AI Agent related endpoints
This handles HTTP requests and delegates to service layer
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
import logging

from ..service.agent_service import AgentService
from ..validation.travel_validation import (
    ChatMessageValidation,
    AgentStatusValidation,
    AgentInteractionValidation
)


class AgentView:
    """View class for AI Agent API endpoints"""

    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def chat_with_agent(request):
        """
        Send a chat message to the AI Agent

        Expected payload:
        {
            "message": "I want to travel to Japan",
            "user_id": "user123",
            "session_id": "session456" (optional)
        }
        """
        try:
            # Log request data for debugging
            logger = logging.getLogger(__name__)
            logger.info(f"Received chat request: {request.data}")

            # Handle potential encoding issues
            try:
                # Validate request data
                validation = ChatMessageValidation(data=request.data)
                validation.is_valid(raise_exception=True)
            except Exception as validation_error:
                logger.error(f"Validation error: {validation_error}")
                logger.error(f"Request data type: {type(request.data)}")
                logger.error(f"Request data content: {request.data}")
                raise

            # Extract validated data
            message = validation.validated_data['message']
            user_id = validation.validated_data['user_id']
            session_id = validation.validated_data.get('session_id')

            logger.info(f"Processing message: '{message[:100]}...' for user: {user_id}")

            # Initialize service and process chat
            agent_service = AgentService()
            result = agent_service.process_chat_message(message, user_id, session_id)

            # Ensure proper UTF-8 encoding for response
            if 'data' in result and 'response' in result['data']:
                response_text = result['data']['response']
                if isinstance(response_text, bytes):
                    result['data']['response'] = response_text.decode('utf-8', errors='replace')
                elif not isinstance(response_text, str):
                    result['data']['response'] = str(response_text)

            return Response({
                'success': True,
                'data': result
            }, content_type='application/json; charset=utf-8')

        except ValidationError as e:
            logger.error(f"Validation error in chat_with_agent: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in chat_with_agent: {e}")
            return Response({
                'success': False,
                'error': 'Unable to process chat message'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def get_agent_status(request):
        """
        Get status information about the AI Agent system

        Query parameters:
        - include_sub_agents: boolean (default: true)
        - include_tools_status: boolean (default: false)
        - detailed_info: boolean (default: false)
        """
        try:
            # Validate query parameters
            validation = AgentStatusValidation(data=request.query_params)
            validation.is_valid(raise_exception=True)

            # Get agent status
            agent_service = AgentService()
            agent_status = agent_service.get_agent_status()

            # Include sub-agents if requested
            if validation.validated_data.get('include_sub_agents', True):
                agent_status['sub_agents'] = agent_service.get_available_sub_agents()

            # Include tools status if requested
            if validation.validated_data.get('include_tools_status', False):
                from ..service.travel_service import TravelService
                travel_service = TravelService()
                agent_status['tools_status'] = travel_service.get_travel_tools_status()

            # Include detailed info if requested
            if validation.validated_data.get('detailed_info', False):
                agent_status['configuration'] = agent_service.validate_agent_configuration()

            return Response({
                'success': True,
                'data': agent_status
            })

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error in get_agent_status: {e}")
            return Response({
                'success': False,
                'error': 'Unable to get agent status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    @permission_classes([AllowAny])
    def list_sub_agents(request):
        """
        List all available sub-agents

        Query parameters:
        - include_status: boolean (default: true)
        - include_capabilities: boolean (default: false)
        """
        try:
            # Get sub-agents
            agent_service = AgentService()
            sub_agents = agent_service.get_available_sub_agents()

            return Response({
                'success': True,
                'data': sub_agents
            })

        except Exception as e:
            logging.getLogger(__name__).error(f"Error in list_sub_agents: {e}")
            return Response({
                'success': False,
                'error': 'Unable to list sub-agents'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def agent_interaction(request):
        """
        Handle complex agent interactions

        Expected payload:
        {
            "interaction_type": "planning|booking|recommendation",
            "parameters": {...},
            "user_context": {...}
        }
        """
        try:
            # Validate request data
            validation = AgentInteractionValidation(data=request.data)
            validation.is_valid(raise_exception=True)

            # Extract validated data
            interaction_type = validation.validated_data['interaction_type']
            parameters = validation.validated_data.get('parameters', {})
            user_context = validation.validated_data.get('user_context', {})

            # Initialize service and process interaction
            agent_service = AgentService()
            result = agent_service.process_complex_interaction(
                interaction_type, parameters, user_context
            )

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
            logging.getLogger(__name__).error(f"Error in agent_interaction: {e}")
            return Response({
                'success': False,
                'error': 'Unable to process agent interaction'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function-based views for backward compatibility
def chat_with_agent(request):
    return AgentView.chat_with_agent(request)


def get_agent_status(request):
    return AgentView.get_agent_status(request)


def list_sub_agents(request):
    return AgentView.list_sub_agents(request)


def agent_interaction(request):
    return AgentView.agent_interaction(request)