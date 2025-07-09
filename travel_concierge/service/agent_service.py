"""
Service layer for AI Agent functionality
This service wraps the root_agent and provides business logic for AI interactions
"""

import logging
import time
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

            # Validate and enhance response structure
            enhanced_response = self._enhance_response_structure(response)

            return {
                'success': True,
                'response': enhanced_response,
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

            # Import required modules for AI agent interaction
            import asyncio
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
            from google.genai import types

            # Initialize services
            session_service = InMemorySessionService()
            artifacts_service = InMemoryArtifactService()

            # Create session if not provided
            if not session_id:
                session_id = f"session_{user_id}_{int(time.time())}"

            session = session_service.create_session(
                state={},
                app_name="travel-concierge",
                user_id=user_id
            )

            # Create content for the message
            content = types.Content(role="user", parts=[types.Part(text=message)])

            # Create runner with root agent
            runner = Runner(
                app_name="travel-concierge",
                agent=self.root_agent,
                artifact_service=artifacts_service,
                session_service=session_service,
            )

            # Run the agent asynchronously
            events_async = runner.run_async(
                session_id=session.id,
                user_id=user_id,
                new_message=content
            )

            # Collect response
            response_parts = []
            async def collect_response():
                async for event in events_async:
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_parts.append(part.text)
                            # Handle function responses that might contain map_url and image_url
                            if part.function_response:
                                response_parts.append(str(part.function_response.response))
                return "\n".join(response_parts)

                        # Run the async function
            try:
                response = asyncio.run(collect_response())
            except RuntimeError as e:
                # Handle case where event loop is already running
                if "event loop is running" in str(e):
                    # Create new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        response = loop.run_until_complete(collect_response())
                    finally:
                        loop.close()
                else:
                    raise e

            if not response:
                response = f"Agent response to: {message}"

            return response

        except (ValueError, RuntimeError) as e:
            # Handle specific OpenTelemetry context errors
            if "different Context" in str(e) or "context" in str(e).lower():
                self.logger.warning(f"OpenTelemetry context issue ignored: {e}")
                return f"Agent response to: {message} (context issue handled)"
            raise
        except Exception as e:
            self.logger.error(f"Error in agent interaction: {e}")
            # Fallback to simple response if AI agent fails
            return f"Agent response to: {message} (fallback due to error: {str(e)})"

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

    def _enhance_response_structure(self, response: str) -> str:
        """
        Enhance response structure to ensure consistent format for mobile app parsing
        """
        try:
            # Ensure Day format is consistent
            import re

            # Replace any "Ngày X" with "Day X" for mobile app compatibility
            response = re.sub(r'Ngày\s*(\d+)', r'Day \1', response, flags=re.IGNORECASE)
            response = re.sub(r'Ngày\s*(\d+)', r'Day \1', response, flags=re.IGNORECASE)

            # Replace other language variations
            response = re.sub(r'Jour\s*(\d+)', r'Day \1', response, flags=re.IGNORECASE)
            response = re.sub(r'Día\s*(\d+)', r'Day \1', response, flags=re.IGNORECASE)
            response = re.sub(r'Tag\s*(\d+)', r'Day \1', response, flags=re.IGNORECASE)

            # Ensure map_url and image_url are mentioned if they exist in the response
            if 'map_url' in response and 'image_url' in response:
                # Response already has the required fields
                pass
            else:
                # Add note about missing fields for debugging
                self.logger.info("Response may be missing map_url or image_url fields")

            return response

        except Exception as e:
            self.logger.warning(f"Error enhancing response structure: {e}")
            return response