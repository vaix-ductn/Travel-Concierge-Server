from rest_framework import serializers

class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer for all models.
    Override this class for custom validation, to_representation, etc.
    """
    class Meta:
        abstract = True