from rest_framework import serializers
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from ..models.user_profile import UserProfile
from base.serializers.base import BaseSerializer


class UserProfileSerializer(BaseSerializer):
    """Serializer for reading user profile data"""
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        exclude = ['user_profile_uuid', 'created_at', 'updated_at']
        read_only_fields = ['user_profile_uuid', 'created_at', 'updated_at']
        # Các trường mới sẽ tự động thêm vào output

    def get_username(self, obj):
        return obj.user_uuid.username if obj.user_uuid else None

    def get_email(self, obj):
        return obj.user_uuid.email if obj.user_uuid else None

    def get_full_name(self, obj):
        return obj.user_uuid.full_name if obj.user_uuid else None


class UserProfileUpdateSerializer(BaseSerializer):
    """Serializer for updating user profile data with validation"""
    email = serializers.EmailField(validators=[EmailValidator()])
    username = serializers.CharField(max_length=100)
    interests = serializers.CharField(allow_blank=True)
    address = serializers.CharField(allow_blank=True)
    # Extended fields validation
    passport_nationality = serializers.CharField(max_length=100, required=False, allow_blank=True)
    seat_preference = serializers.CharField(max_length=50, required=False, allow_blank=True)
    food_preference = serializers.CharField(required=False, allow_blank=True)
    allergies = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    likes = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    dislikes = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    price_sensitivity = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    home_address = serializers.CharField(required=False, allow_blank=True)
    local_prefer_mode = serializers.CharField(max_length=50, required=False, allow_blank=True)
    class Meta:
        model = UserProfile
        exclude = ['user_profile_uuid', 'created_at', 'updated_at']
    def validate_email(self, value):
        if value:
            instance = getattr(self, 'instance', None)
            if UserProfile.objects.filter(email=value).exclude(pk=instance.pk if instance else None).exists():
                raise serializers.ValidationError("Email already exists")
        return value
    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores")
        return value
    def validate_avatar_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Avatar URL must be a valid HTTP/HTTPS URL")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one digit")
        return value
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New password and confirmation do not match")
        return attrs


class UserProfileCreateSerializer(BaseSerializer):
    """Serializer for creating new user profiles"""
    password = serializers.CharField(write_only=True)
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'password', 'address', 'interests', 'avatar_url',
            'passport_nationality', 'seat_preference', 'food_preference', 'allergies',
            'likes', 'dislikes', 'price_sensitivity', 'home_address', 'local_prefer_mode'
        ]
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    def create(self, validated_data):
        password = validated_data.pop('password')
        user_profile = UserProfile(**validated_data)
        user_profile.set_password(password)
        user_profile.save()
        return user_profile