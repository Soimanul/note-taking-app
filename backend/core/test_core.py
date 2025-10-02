import uuid
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Document, GeneratedContent, Log
from .tasks import process_document
from unittest.mock import patch, MagicMock

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
        self.client.login(username='user1', password='password123')
        response = self.client.get('/api/documents/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Should only see doc1
        self.assertEqual(response.data[0]['filename'], 'doc1.pdf')

    def test_unauthenticated_access_is_denied(self):
        """Ensure unauthenticated users cannot access any document endpoint."""
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_see_other_users_documents(self):
        """Ensure listing documents is properly scoped to the logged-in user."""
        self.client.login(username='user2', password='password123')
        response = self.client.get('/api/documents/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0) # user2 has no documents, should not see doc1

    def test_retrieve_own_document(self):
        """Ensure a user can retrieve their own document by ID."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(f'/api/documents/{self.doc1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filename'], self.doc1.filename)

    def test_cannot_retrieve_other_users_document(self):
        """Ensure a user gets a 404 when trying to access another user's document."""
        self.client.login(username='user2', password='password123')
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
    @patch('core.tasks.pinecone_index')
    @patch('core.tasks.sentence_transformer_model')
    @patch('core.tasks.gemini_api')
    @patch('core.tasks.parse_text_from_file')
    def test_process_document_success_path(self, mock_parse, mock_gemini, mock_sentence, mock_pinecone):
        """
        Test the successful execution of the `process_document` task.
        """
        # Configure the return values of our mocks
        mock_parse.return_value = "This is the extracted text from the document."
        mock_gemini.generate_content.return_value = {"markdown_text": "This is a summary."}
        mock_sentence.encode.return_value = [0.1, 0.2, 0.3] # Fake embedding vector
        
        # Run the Celery task synchronously for testing
        process_document(self.document.id)

        # Refresh the document object from the database to see changes
        self.document.refresh_from_db()

        # Assertions: Check if the task did what it was supposed to
        self.assertEqual(self.document.status, 'completed')
        
        # Check that a 'summary' was created
        self.assertTrue(GeneratedContent.objects.filter(document=self.document, contentType='summary').exists())
        
        # Check that a success log was created
        self.assertTrue(Log.objects.filter(document=self.document, level='INFO').exists())

        # Check that our mocks were called
        mock_parse.assert_called_once_with(self.document.filepath, self.document.fileType)
        mock_gemini.generate_content.assert_called_once()
        mock_sentence.encode.assert_called_once()
        mock_pinecone.upsert.assert_called_once()

    @patch('core.tasks.parse_text_from_file')
    def test_process_document_failure_path(self, mock_parse):
        """
        Test the failure path of the `process_document` task (e.g., parsing fails).
        """
        # Configure the mock to raise an exception, simulating a failure
        mock_parse.side_effect = Exception("Failed to parse PDF")

        # Run the task
        process_document(self.document.id)

        # Refresh the document object from the database
        self.document.refresh_from_db()

        # Assertions: Check for failure state
        self.assertEqual(self.document.status, 'failed')
        
        # Check that an ERROR log was created
        log_entry = Log.objects.get(document=self.document, level='ERROR')
        self.assertIn("Failed to parse PDF", log_entry.message)