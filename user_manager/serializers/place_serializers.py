from rest_framework import serializers

class PlaceCreateSerializer(serializers.Serializer):
    user_uuid = serializers.UUIDField()
    place_name = serializers.CharField(max_length=255)
    address = serializers.CharField(max_length=500)
    lat = serializers.CharField(max_length=50)
    long = serializers.CharField(max_length=50)
    review_ratings = serializers.CharField(max_length=20)
    highlights = serializers.CharField(max_length=1000)
    image_url = serializers.CharField(max_length=500)
    map_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    place_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class PlaceReadSerializer(serializers.Serializer):
    place_uuid = serializers.UUIDField(read_only=True)
    user_uuid = serializers.UUIDField(source='user_uuid.user_uuid', read_only=True)
    place_name = serializers.CharField()
    address = serializers.CharField()
    lat = serializers.CharField()
    long = serializers.CharField()
    review_ratings = serializers.CharField()
    highlights = serializers.CharField()
    image_url = serializers.CharField()
    map_url = serializers.CharField()
    place_id = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

class PlaceUpdateSerializer(serializers.Serializer):
    place_name = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(max_length=500, required=False)
    lat = serializers.CharField(max_length=50, required=False)
    long = serializers.CharField(max_length=50, required=False)
    review_ratings = serializers.CharField(max_length=20, required=False)
    highlights = serializers.CharField(max_length=1000, required=False)
    image_url = serializers.CharField(max_length=500, required=False)
    map_url = serializers.CharField(max_length=500, required=False)
    place_id = serializers.CharField(max_length=100, required=False)