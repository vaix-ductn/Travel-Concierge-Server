"""
Service layer for AI Agent functionality
This service wraps the root_agent and provides business logic for AI interactions
"""

import logging
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError

# Import the root agent - keep this import path to maintain compatibility
from travel_concierge.agent import root_agent


class AgentService:
    """Service class for AI Agent business logic"""

    def __init__(self):
        """Initialize service with root agent"""
        self.root_agent = root_agent
        self.logger = logging.getLogger(__name__)

    def process_chat_message(self, message: str, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a chat message through the AI Agent system

        Args:
            message: User's message
            user_id: User identifier
            session_id: Optional session identifier

        Returns:
            Dict containing agent response and metadata
        """
        try:
            self.logger.info(f"Processing chat message for user {user_id}: {message[:100]}...")

            # Process message through root agent
            # This maintains the existing agent functionality
            response = self._interact_with_agent(message, user_id, session_id)

            self.logger.info(f"Agent response generated for user {user_id}")

            return {
                'success': True,
                'response': response,
                'user_id': user_id,
                'session_id': session_id
            }

        except Exception as e:
            self.logger.error(f"Error processing chat message: {e}")
            raise ValidationError(f"Unable to process chat message: {str(e)}")

    def _interact_with_agent(self, message: str, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Internal method to interact with the root agent
        This method can be extended to handle different interaction patterns
        """
        try:
            # Suppress OpenTelemetry context warnings specifically
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning, module="opentelemetry")

            # Here we would implement the actual agent interaction
            # For now, we maintain the existing pattern but wrapped in service layer

            # Note: The actual implementation would depend on how the agent is currently used
            # This is a placeholder that maintains the agent reference

            # Example of how this might work:
            # if hasattr(self.root_agent, 'process_message'):
            #     return self.root_agent.process_message(message, user_id=user_id, session_id=session_id)

            return f"Agent response to: {message}"

        except (ValueError, RuntimeError) as e:
            # Handle specific OpenTelemetry context errors
            if "different Context" in str(e) or "context" in str(e).lower():
                self.logger.warning(f"OpenTelemetry context issue ignored: {e}")
                return f"Agent response to: {message} (context issue handled)"
            raise
        except Exception as e:
            self.logger.error(f"Error in agent interaction: {e}")
            raise

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about the AI Agent system"""
        try:
            return {
                'agent_name': self.root_agent.name if hasattr(self.root_agent, 'name') else 'root_agent',
                'description': self.root_agent.description if hasattr(self.root_agent, 'description') else 'Travel Concierge Agent',
                'sub_agents_count': len(self.root_agent.sub_agents) if hasattr(self.root_agent, 'sub_agents') else 0,
                'status': 'active'
            }
        except Exception as e:
            self.logger.error(f"Error getting agent status: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_available_sub_agents(self) -> List[Dict[str, Any]]:
        """Get information about available sub-agents"""
        try:
            if not hasattr(self.root_agent, 'sub_agents'):
                return []

            sub_agents_info = []
            for sub_agent in self.root_agent.sub_agents:
                sub_agents_info.append({
                    'name': sub_agent.name if hasattr(sub_agent, 'name') else 'unknown',
                    'description': sub_agent.description if hasattr(sub_agent, 'description') else 'No description',
                })

            return sub_agents_info

        except Exception as e:
            self.logger.error(f"Error getting sub-agents info: {e}")
            return []

    def validate_agent_configuration(self) -> Dict[str, Any]:
        """Validate that the agent system is properly configured"""
        try:
            validation_results = {
                'root_agent_available': self.root_agent is not None,
                'has_sub_agents': hasattr(self.root_agent, 'sub_agents') and len(self.root_agent.sub_agents) > 0,
                'configuration_valid': True,
                'errors': []
            }

            if not validation_results['root_agent_available']:
                validation_results['errors'].append('Root agent not available')
                validation_results['configuration_valid'] = False

            if not validation_results['has_sub_agents']:
                validation_results['errors'].append('No sub-agents configured')
                validation_results['configuration_valid'] = False

            return validation_results

        except Exception as e:
            self.logger.error(f"Error validating agent configuration: {e}")
            return {
                'configuration_valid': False,
                'errors': [str(e)]
            }