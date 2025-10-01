from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Document, GeneratedContent, Log

# ==============================================================================
#  User Serializer
# ==============================================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model. Excludes sensitive data like the password.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


# ==============================================================================
#  Document Serializer
# ==============================================================================
class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Document model.
    It will serialize all fields defined in the model.
    """
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['user', 'status'] # User and status are set by the server, not the client.


# ==============================================================================
#  GeneratedContent Serializer
# ==============================================================================
class GeneratedContentSerializer(serializers.ModelSerializer):
    """
    Serializer for the GeneratedContent model.
    """
    class Meta:
        model = GeneratedContent
        fields = '__all__'


# ==============================================================================
#  Log Serializer
# ==============================================================================
class LogSerializer(serializers.ModelSerializer):
    """
    Serializer for the Log model.
    """
    class Meta:
        model = Log
        fields = '__all__'

