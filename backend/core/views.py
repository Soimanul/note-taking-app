from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Document, GeneratedContent, Log
from .serializers import DocumentSerializer, UserSerializer

# ==============================================================================
#  1. User Registration View
# ==============================================================================
class UserCreate(generics.CreateAPIView):
    """
    Creates a new user.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

# ==============================================================================
#  2. Document List & Create View
# ==============================================================================
class DocumentListCreate(generics.ListCreateAPIView):
    """
    Handles GET and POST requests for docs only from authenticated users.
    """

    def get_queryset(self):
        """
        This view should only return documents owned by the currently authenticated user.
        """
        return Document.objects.filter(user=self.request.user).order_by('-uploadDate')

    def perform_create(self, serializer):
        """
        This view assigns the user automatically when a new doc is created.
        """

        serializer.save(user=self.request.user)