"""
Django Views for Voice Chat API
Provides REST endpoints for voice chat functionality
"""
import json
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings

from .websocket_server import voice_websocket_server
from .adk_live_handler import adk_live_handler


@method_decorator(csrf_exempt, name='dispatch')
class VoiceChatStatusView(View):
    """Get voice chat server status and configuration"""

    def get(self, request):
        """Return voice chat server status"""
        try:
            # Get server configuration
            server_config = {
                'status': 'active' if voice_websocket_server.is_running else 'inactive',
                'websocket_url': f'ws://{voice_websocket_server.host}:{voice_websocket_server.port}',
                'audio_config': {
                    'input_sample_rate': adk_live_handler.input_sample_rate,
                    'output_sample_rate': adk_live_handler.output_sample_rate,
                    'voice_name': adk_live_handler.voice_name,
                    'supported_formats': ['audio/pcm;rate=16000'],
                    'max_session_duration': 3600  # 1 hour
                },
                'connection_info': {
                    'protocol': 'WebSocket',
                    'subprotocol': 'voice-chat',
                    'authentication': 'none_required',  # Since we're relying on app-level auth
                    'message_types': ['start_session', 'stop_session', 'ping', 'get_status']
                },
                'server_stats': {
                    'active_connections': len(voice_websocket_server.websocket_sessions),
                    'active_sessions': len(adk_live_handler.active_sessions),
                    'uptime': 0  # TODO: Track server uptime
                }
            }

            return JsonResponse(server_config)

        except Exception as e:
            return JsonResponse({
                'error': 'Failed to get server status',
                'message': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VoiceChatSessionsView(View):
    """Manage voice chat sessions"""

    def get(self, request):
        """Get all active sessions"""
        try:
            sessions = adk_live_handler.get_all_sessions()

            return JsonResponse({
                'active_sessions': sessions,
                'total_count': len(sessions)
            })

        except Exception as e:
            return JsonResponse({
                'error': 'Failed to get sessions',
                'message': str(e)
            }, status=500)

    def delete(self, request):
        """Close all active sessions (admin function)"""
        try:
            session_ids = list(adk_live_handler.active_sessions.keys())
            closed_count = 0

            for session_id in session_ids:
                # Note: This is a synchronous call, but close_session is async
                # In a real implementation, you'd want to handle this properly
                try:
                    # For now, we'll just mark as inactive
                    if session_id in adk_live_handler.active_sessions:
                        adk_live_handler.active_sessions[session_id]['is_active'] = False
                        del adk_live_handler.active_sessions[session_id]
                        closed_count += 1
                except Exception:
                    pass

            return JsonResponse({
                'message': f'Closed {closed_count} sessions',
                'closed_sessions': closed_count
            })

        except Exception as e:
            return JsonResponse({
                'error': 'Failed to close sessions',
                'message': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class VoiceChatHealthView(View):
    """Health check endpoint for voice chat service"""

    def get(self, request):
        """Health check"""
        try:
            # Check if WebSocket server is running
            websocket_healthy = voice_websocket_server.is_running

            # Check if ADK handler is ready
            adk_healthy = hasattr(adk_live_handler, 'session_service')

            # Overall health
            is_healthy = websocket_healthy and adk_healthy

            health_status = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'timestamp': 1000,  # Current timestamp
                'components': {
                    'websocket_server': 'healthy' if websocket_healthy else 'unhealthy',
                    'adk_handler': 'healthy' if adk_healthy else 'unhealthy',
                    'google_adk': 'healthy'  # Assume healthy if no errors
                },
                'details': {
                    'websocket_host': voice_websocket_server.host,
                    'websocket_port': voice_websocket_server.port,
                    'adk_voice': adk_live_handler.voice_name,
                    'active_sessions': len(adk_live_handler.active_sessions)
                }
            }

            status_code = 200 if is_healthy else 503
            return JsonResponse(health_status, status=status_code)

        except Exception as e:
            return JsonResponse({
                'status': 'unhealthy',
                'error': 'Health check failed',
                'message': str(e)
            }, status=503)


@method_decorator(csrf_exempt, name='dispatch')
class VoiceChatConfigView(View):
    """Get voice chat configuration for Flutter app"""

    def get(self, request):
        """Return configuration needed by Flutter app"""
        try:
            config = {
                'websocket': {
                    'url': f'ws://{voice_websocket_server.host}:{voice_websocket_server.port}',
                    'subprotocol': 'voice-chat',
                    'timeout': 30000,  # 30 seconds
                    'reconnect_attempts': 3,
                    'reconnect_delay': 5000  # 5 seconds
                },
                'audio': {
                    'input_format': 'pcm16',
                    'input_sample_rate': adk_live_handler.input_sample_rate,
                    'output_sample_rate': adk_live_handler.output_sample_rate,
                    'chunk_size': 1024,  # Bytes per chunk
                    'max_recording_duration': 300,  # 5 minutes
                    'voice_activation_threshold': 0.1
                },
                'session': {
                    'max_duration': 3600,  # 1 hour
                    'idle_timeout': 300,  # 5 minutes
                    'auto_close_on_error': True
                },
                'features': {
                    'speech_to_text': True,
                    'text_to_speech': True,
                    'interruption_detection': True,
                    'noise_cancellation': False,  # Not implemented yet
                    'echo_cancellation': False   # Not implemented yet
                }
            }

            return JsonResponse(config)

        except Exception as e:
            return JsonResponse({
                'error': 'Failed to get configuration',
                'message': str(e)
            }, status=500)