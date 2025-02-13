# backend/api/serializers.py
from rest_framework import serializers
from .models import User, Track, License
from django.contrib.auth import get_user_model
import uuid

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'password')  # Include password for creation
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user

class TrackSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')  # Show username, read-only

    class Meta:
        model = Track
        fields = ('id', 'user', 'title', 'genre', 'bpm', 'key', 'file_path', 'preview_path')
        read_only_fields = ('file_path', 'preview_path') #Make sure the user does not input

class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ('id', 'track', 'user', 'license_type', 'price', 'agreement_text', 'file_path')