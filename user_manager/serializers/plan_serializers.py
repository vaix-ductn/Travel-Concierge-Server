from rest_framework import serializers

class ActivitySerializer(serializers.Serializer):
    time_slot = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    weather_icon = serializers.CharField(max_length=10, required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)

class ItineraryDaySerializer(serializers.Serializer):
    day_number = serializers.IntegerField(min_value=1)
    date = serializers.DateTimeField()
    display_date = serializers.CharField(max_length=50)
    activities = ActivitySerializer(many=True)

class PlanMetadataSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField()
    days_count = serializers.IntegerField(min_value=1)

class PlanCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    destination = serializers.CharField(max_length=255)
    itinerary = ItineraryDaySerializer(many=True)
    metadata = PlanMetadataSerializer()

class PlanReadSerializer(serializers.Serializer):
    plan_uuid = serializers.UUIDField(read_only=True)
    user_uuid = serializers.UUIDField(source='user_uuid.user_uuid', read_only=True)
    title = serializers.CharField()
    destination = serializers.CharField()
    itinerary = serializers.JSONField()
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

class PlanUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    destination = serializers.CharField(max_length=255, required=False)
    itinerary = ItineraryDaySerializer(many=True, required=False)
    metadata = PlanMetadataSerializer(required=False)