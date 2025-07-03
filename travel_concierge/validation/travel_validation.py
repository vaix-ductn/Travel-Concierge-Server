"""
Validation classes for Travel Concierge app
These handle validation logic separate from serializers
"""

import re
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class BaseValidation(serializers.Serializer):
    """Base validation class with common validation methods"""

    def validate_max_length(self, value, max_length=255):
        """Validate string max length"""
        if value and len(value) > max_length:
            raise serializers.ValidationError(f'Maximum length is {max_length} characters')
        return True

    def validate_non_empty_string(self, value, field_name="field"):
        """Validate that string is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(f'{field_name} cannot be empty')
        return True


class ChatMessageValidation(BaseValidation):
    """Validation for chat messages sent to AI Agent"""

    message = serializers.CharField(required=True, max_length=5000)
    user_id = serializers.CharField(required=True, max_length=255)
    session_id = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_message(self, value):
        """Validate chat message content"""
        if self.validate_non_empty_string(value, "Message"):
            # Check for potentially harmful content
            if self._contains_harmful_content(value):
                raise serializers.ValidationError("Message contains inappropriate content")
            return value

    def validate_user_id(self, value):
        """Validate user ID format"""
        if self.validate_non_empty_string(value, "User ID"):
            # Simple validation for user ID format
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', value):
                raise serializers.ValidationError("User ID contains invalid characters")
            return value

    def _contains_harmful_content(self, message: str) -> bool:
        """Check for potentially harmful content in messages"""
        # Basic content filtering - can be expanded
        harmful_patterns = [
            r'<script',
            r'javascript:',
            r'onclick=',
            r'onerror=',
        ]

        message_lower = message.lower()
        for pattern in harmful_patterns:
            if re.search(pattern, message_lower):
                return True
        return False


class TravelRecommendationValidation(BaseValidation):
    """Validation for travel recommendation requests"""

    destination_type = serializers.CharField(required=True, max_length=100)
    budget_range = serializers.CharField(required=True, max_length=50)
    travel_dates = serializers.CharField(required=False, allow_blank=True, max_length=100)
    group_size = serializers.IntegerField(required=False, min_value=1, max_value=50)
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    special_requirements = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_destination_type(self, value):
        """Validate destination type"""
        valid_types = [
            'beach', 'mountain', 'city', 'countryside', 'adventure',
            'cultural', 'relaxation', 'business', 'family', 'romantic'
        ]

        if value.lower() not in valid_types:
            raise serializers.ValidationError(
                f"Invalid destination type. Must be one of: {', '.join(valid_types)}"
            )
        return value.lower()

    def validate_budget_range(self, value):
        """Validate budget range"""
        valid_ranges = ['budget', 'mid-range', 'luxury', 'ultra-luxury']

        if value.lower() not in valid_ranges:
            raise serializers.ValidationError(
                f"Invalid budget range. Must be one of: {', '.join(valid_ranges)}"
            )
        return value.lower()

    def validate_travel_dates(self, value):
        """Validate travel dates format"""
        if value:
            # Basic date format validation - can be expanded
            if len(value) > 100:
                raise serializers.ValidationError("Travel dates description too long")
        return value

    def validate_special_requirements(self, value):
        """Validate special requirements"""
        if value and self.validate_max_length(value, 1000):
            return value
        return value


class AgentStatusValidation(BaseValidation):
    """Validation for agent status requests"""

    include_sub_agents = serializers.BooleanField(required=False, default=True)
    include_tools_status = serializers.BooleanField(required=False, default=False)
    detailed_info = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        """Cross-field validation for agent status requests"""
        # No specific cross-field validation needed for now
        return attrs


class AgentInteractionValidation(BaseValidation):
    """Validation for complex agent interactions"""

    interaction_type = serializers.CharField(required=True, max_length=50)
    parameters = serializers.JSONField(required=False, default=dict)
    user_context = serializers.JSONField(required=False, default=dict)

    def validate_interaction_type(self, value):
        """Validate interaction type"""
        valid_types = [
            'chat', 'recommendation', 'planning', 'booking',
            'inspiration', 'pre_trip', 'in_trip', 'post_trip'
        ]

        if value.lower() not in valid_types:
            raise serializers.ValidationError(
                f"Invalid interaction type. Must be one of: {', '.join(valid_types)}"
            )
        return value.lower()

    def validate_parameters(self, value):
        """Validate interaction parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a valid JSON object")

        # Validate parameter size
        if len(str(value)) > 10000:
            raise serializers.ValidationError("Parameters too large")

        return value

    def validate_user_context(self, value):
        """Validate user context"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("User context must be a valid JSON object")

        # Validate context size
        if len(str(value)) > 5000:
            raise serializers.ValidationError("User context too large")

        return value


class ToolsStatusValidation(BaseValidation):
    """Validation for tools status requests"""

    tool_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    include_health_check = serializers.BooleanField(required=False, default=True)
    detailed_status = serializers.BooleanField(required=False, default=False)

    def validate_tool_names(self, value):
        """Validate tool names"""
        valid_tools = ['places', 'search', 'memory', 'all']

        for tool_name in value:
            if tool_name.lower() not in valid_tools:
                raise serializers.ValidationError(
                    f"Invalid tool name '{tool_name}'. Must be one of: {', '.join(valid_tools)}"
                )

        return [tool.lower() for tool in value]