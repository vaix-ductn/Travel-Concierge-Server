"""
View layer for AI Agent related endpoints
This handles HTTP requests and delegates to service layer
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
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
            # Validate request data
            validation = ChatMessageValidation(data=request.data)
            validation.is_valid(raise_exception=True)

            # Extract validated data
            message = validation.validated_data['message']
            user_id = validation.validated_data['user_id']
            session_id = validation.validated_data.get('session_id')

            # Initialize service and process chat
            agent_service = AgentService()
            result = agent_service.process_chat_message(message, user_id, session_id)

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
            logging.getLogger(__name__).error(f"Error in chat_with_agent: {e}")
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
        Get list of available sub-agents
        """
        try:
            agent_service = AgentService()
            sub_agents = agent_service.get_available_sub_agents()

            return Response({
                'success': True,
                'data': {
                    'sub_agents': sub_agents,
                    'count': len(sub_agents)
                }
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
        Complex agent interaction endpoint

        Expected payload:
        {
            "interaction_type": "planning",
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

            # Process interaction (placeholder for now)
            # This would be implemented based on specific interaction types
            result = {
                'interaction_type': interaction_type,
                'processed': True,
                'parameters_received': parameters,
                'user_context_received': user_context,
                'message': f'Processed {interaction_type} interaction'
            }

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


# Function-based views for URL routing
def chat_with_agent(request):
    """Function wrapper for chat with agent"""
    return AgentView.chat_with_agent(request)

def get_agent_status(request):
    """Function wrapper for get agent status"""
    return AgentView.get_agent_status(request)

def list_sub_agents(request):
    """Function wrapper for list sub agents"""
    return AgentView.list_sub_agents(request)

def agent_interaction(request):
    """Function wrapper for agent interaction"""
    return AgentView.agent_interaction(request)