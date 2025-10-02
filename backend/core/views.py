from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import FileSystemStorage
import os

from .models import Document
from .serializers import DocumentSerializer, UserSerializer

from .tasks import process_document

# ==============================================================================
# 0. Custom Permissions
# ==============================================================================
class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or view it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner of the document.
        return obj.user == request.user


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

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """
        This view should only return documents owned by the currently authenticated user.
        """
        return Document.objects.filter(user=self.request.user).order_by("-uploadDate")

    def create(self, request, *args, **kwargs):
        """
        Overries  default create method to handle file upload, save its metadata, and triggerthe assync processing task
        """
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "No file was provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Save the file locally
        fs = FileSystemStorage(location="media/uploads/")
        filename = fs.get_available_name(uploaded_file.name)
        saved_path = fs.save(filename, uploaded_file)
        filepath = os.path.abspath(fs.path(saved_path))

        # Prepare the data for the serializer
        data_for_serializer = {
            "filename": uploaded_file.name,
            "filepath": filepath,
            "fileType": os.path.splitext(uploaded_file.name)[1].lower().strip("."),
            "size": uploaded_file.size,
        }

        serializer = self.get_serializer(data=data_for_serializer)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        new_document_id = serializer.instance.id

        process_document.delay(str(new_document_id))

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        """
        This view assigns the user automatically when a new doc is created.
        """

        serializer.save(user=self.request.user)


# ==============================================================================
#  3. Document Detail, Update & Delete View
# ==============================================================================
class DocumentRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles GET, PUT/PATCH, and DELETE requests for a single document.
    """

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        This view should only return documents owned by the currently authenticated user.
        """
        return Document.objects.filter(user=self.request.user)
