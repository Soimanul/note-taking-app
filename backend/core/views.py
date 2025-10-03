import os
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status

User = get_user_model()
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile
from django.db import models

from .models import Document
from .serializers import DocumentSerializer, UserSerializer
from .tasks import process_document, generate_summary_from_notes, generate_quiz_from_notes
from . import services

# ==============================================================================
#  -1. Helper Functions
# ==============================================================================


def _save_uploaded_file(uploaded_file: UploadedFile) -> dict:
    """
    Saves the uploaded file to the local filesystem and returns its metadata.
    """

    fs = FileSystemStorage(location="media/uploads/")
    filename = fs.get_available_name(uploaded_file.name)
    saved_path = fs.save(filename, uploaded_file)
    filepath = os.path.abspath(fs.path(saved_path))

    return {
        "filename": uploaded_file.name,
        "filepath": filepath,
        "fileType": os.path.splitext(uploaded_file.name)[1].lower().strip("."),
        "size": uploaded_file.size,
    }


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
    
    def create(self, request, *args, **kwargs):
        print(f"Registration request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            print(f"User created successfully: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"User creation failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        1. Saves the file.
        2. Creates the database record.
        3. Triggers the async processing task.        
        """
        
        # Save the file locally
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"detail": "No file was provided."}, status=status.HTTP_400_BAD_REQUEST)

        file_metadata = _save_uploaded_file(uploaded_file)
        
        serializer = self.get_serializer(data=file_metadata)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        new_document_id = serializer.instance.id
        process_document.delay(str(new_document_id))

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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


# ==============================================================================
#  4. Semantic Search Implementation
# ==============================================================================
class SemanticSearchView(APIView):
    """
    Handles semantic search queries for documents.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', None)
        if not query:
            return Response({"detail": "A search query parameter 'q' is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate an embedding for the search query to compare with
        query_embedding = services.embedding_model.encode(query).tolist()

        # Query Pinecone DB to find the most similar document vectors
        results = services.pinecone_index.query(
            vector=query_embedding,
            top_k=5, 
            filter={'user_id': str(request.user.id)}
        )
        
        match_ids = [match['id'] for match in results.get('matches', [])]
        if not match_ids:
            return Response([], status=status.HTTP_200_OK)

        # Retrieve the full document objects from PostgreSQL
        preserved_order = models.Case(*[models.When(pk=pk, then=pos) for pos, pk in enumerate(match_ids)])
        documents = Document.objects.filter(id__in=match_ids).order_by(preserved_order)

        # Serialize the docs and return them
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)


# ==============================================================================
#  5. Content Generation View
# ==============================================================================
class GenerateContentView(APIView):
    """
    Handles on-demand content generation for documents.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def post(self, request, pk):
        content_type = request.data.get('type')
        
        if content_type not in ['summary', 'quiz']:
            return Response(
                {"detail": "Invalid content type. Must be 'summary' or 'quiz'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"detail": "Document not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if notes exist
        from .models import GeneratedContent
        try:
            GeneratedContent.objects.get(document=document, contentType="notes")
        except GeneratedContent.DoesNotExist:
            return Response(
                {"detail": "Document notes must be generated first."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trigger the appropriate Celery task
        if content_type == 'summary':
            generate_summary_from_notes.delay(str(document.id))
        elif content_type == 'quiz':
            generate_quiz_from_notes.delay(str(document.id))

        return Response(
            {"detail": f"{content_type.capitalize()} generation started."}, 
            status=status.HTTP_202_ACCEPTED
        )
