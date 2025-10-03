from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Document, GeneratedContent, Log

User = get_user_model()

# ==============================================================================
#  1. User Serializer
# ==============================================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model. Handles user registration with password hashing.
    """
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
            'email': {'required': True},
            'username': {'required': True}
        }
    
    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password
        )
        return user


# ==============================================================================
#  2. GeneratedContent Serializer
# ==============================================================================
class GeneratedContentSerializer(serializers.ModelSerializer):
    """
    Serializer for the GeneratedContent model.
    """
    class Meta:
        model = GeneratedContent
        fields = '__all__'


# ==============================================================================
#  3. Document Serializer
# ==============================================================================
class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Document model.
    It will serialize all fields defined in the model.
    """
    generated_content = GeneratedContentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['user', 'status'] # User and status are set by the server, not the client.


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

