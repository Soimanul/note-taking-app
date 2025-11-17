import uuid
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from core.models import Document, GeneratedContent, Log
from core.tasks import process_document

# ==============================================================================
#  1. API Tests for Documents
# ==============================================================================
class DocumentAPITests(APITestCase):
    """
    Test suite for the Document API endpoints.
    Covers creation, listing, retrieval, deletion, and permissions.
    """

    def setUp(self):
        # Create two users to test permissions
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

        # Create a document owned by user1
        self.doc1 = Document.objects.create(
            user=self.user1, filename='doc1.pdf', filepath='/fake/path1.pdf', fileType='pdf', size=1024
        )

    def test_list_documents_as_authenticated_user(self):
        """Ensure a user can only list their own documents."""
        # Authenticate using DRF test client's force_authenticate (JWT is default)
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/documents/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Should only see doc1
        self.assertEqual(response.data[0]['filename'], 'doc1.pdf')

    def test_unauthenticated_access_is_denied(self):
        """Ensure unauthenticated users cannot access any document endpoint."""
        # Ensure no authentication is present
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_see_other_users_documents(self):
        """Ensure listing documents is properly scoped to the logged-in user."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/api/documents/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0) # user2 has no documents, should not see doc1

    def test_retrieve_own_document(self):
        """Ensure a user can retrieve their own document by ID."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/documents/{self.doc1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filename'], self.doc1.filename)

    def test_cannot_retrieve_other_users_document(self):
        """Ensure a user gets a 404 when trying to access another user's document."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f'/api/documents/{self.doc1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ==============================================================================
#  2. Tests for the Asynchronous Celery Task
# ==============================================================================
class CeleryTaskTests(APITestCase):
    """
    Test suite for the `process_document` Celery task.
    This uses mocking to simulate external services.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='taskuser', password='password123')
        self.document = Document.objects.create(
            user=self.user,
            filename='celery_test.pdf',
            filepath='/fake/celery_test.pdf',
            fileType='pdf',
            size=4096,
            status='processing'
        )

    # We use @patch to replace external calls with mock objects during the test
    @patch('core.services.pinecone_index')
    @patch('core.services.embedding_model')
    @patch('core.services.ai_adapter')
    @patch('core.tasks.get_parser')
    def test_process_document_success_path(self, mock_get_parser, mock_ai_adapter, mock_embedding, mock_pinecone):
        """
        Test the successful execution of the `process_document` task.
        """
        # Configure the return values of our mocks
        mock_parser = MagicMock()
        mock_parser.parse.return_value = "This is the extracted text from the document."
        mock_get_parser.return_value = mock_parser

        mock_ai_adapter.generate_notes.return_value = "This is a summary."

        # embedding_model.encode(...).tolist() is called in tasks; mock accordingly
        mock_encode_ret = MagicMock()
        mock_encode_ret.tolist.return_value = [0.1, 0.2, 0.3]
        mock_embedding.encode.return_value = mock_encode_ret
        
        # Run the Celery task synchronously for testing
        process_document(self.document.id)

        # Refresh the document object from the database to see changes
        self.document.refresh_from_db()

        # Assertions: Check if the task did what it was supposed to
        self.assertEqual(self.document.status, 'completed')
        
        # Check that 'notes' were created (current processing flow saves notes)
        self.assertTrue(GeneratedContent.objects.filter(document=self.document, contentType='notes').exists())
        
        # Check that a success log was created
        self.assertTrue(Log.objects.filter(document=self.document, level='INFO').exists())

        # Check that our mocks were called
        mock_get_parser.assert_called_once_with(self.document.fileType)
        mock_parser.parse.assert_called_once_with(self.document.filepath)
        mock_ai_adapter.generate_notes.assert_called_once()
        mock_embedding.encode.assert_called_once()
        mock_pinecone.upsert.assert_called_once()

    @patch('core.tasks.get_parser')
    def test_process_document_failure_path(self, mock_get_parser):
        """
        Test the failure path of the `process_document` task (e.g., parsing fails).
        """
        # Configure the parser.parse to raise an exception, simulating a failure
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Failed to parse PDF")
        mock_get_parser.return_value = mock_parser

        # Run the task
        process_document(self.document.id)

        # Refresh the document object from the database
        self.document.refresh_from_db()

        # Assertions: Check for failure state
        self.assertEqual(self.document.status, 'failed')
        
        # Check that an ERROR log was created
        log_entry = Log.objects.get(document=self.document, level='ERROR')
        self.assertIn("Failed to parse PDF", log_entry.message)
