"""URLs for the travel_concierge app."""
from django.urls import path
from .view import agent_view, travel_view
from .voice_chat.views import (
    VoiceChatStatusView,
    VoiceChatSessionsView,
    VoiceChatHealthView,
    VoiceChatConfigView
)

app_name = 'travel_concierge'

urlpatterns = [
    # AI Agent endpoints
    path('chat/', agent_view.chat_with_agent, name='chat'),
    path('status/', agent_view.get_agent_status, name='agent_status'),
    path('sub-agents/', agent_view.list_sub_agents, name='sub_agents'),
    path('interaction/', agent_view.agent_interaction, name='agent_interaction'),

    # Travel endpoints
    path('recommendations/', travel_view.get_travel_recommendations, name='recommendations'),
    path('tools/status/', travel_view.get_tools_status, name='tools_status'),
    path('health/', travel_view.health_check, name='health_check'),

    # Voice Chat endpoints
    path('voice-chat/status/', VoiceChatStatusView.as_view(), name='voice_chat_status'),
    path('voice-chat/sessions/', VoiceChatSessionsView.as_view(), name='voice_chat_sessions'),
    path('voice-chat/health/', VoiceChatHealthView.as_view(), name='voice_chat_health'),
    path('voice-chat/config/', VoiceChatConfigView.as_view(), name='voice_chat_config'),
]