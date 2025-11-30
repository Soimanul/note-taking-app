import io
import os
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import override_settings

from core import views as views_mod
from core import models as models_mod


class ViewsExtraTests(APITestCase):
    def test_save_uploaded_file_and_metadata(self):
        """Test file upload and metadata extraction with filesystem storage."""
        # Create an in-memory uploaded file
        content = b"hello world"
        uploaded = SimpleUploadedFile("test.txt", content, content_type="text/plain")

        meta = views_mod._save_uploaded_file(uploaded)

        assert meta["filename"] == "test.txt"
        assert meta["fileType"] == "txt"
        assert meta["size"] == len(content)

        # Verify the file was actually saved
        assert "uploads/" in meta["filepath"]
        full_path = os.path.join(settings.MEDIA_ROOT, meta["filepath"])
        assert os.path.exists(full_path)

        # Verify file content
        with open(full_path, 'rb') as f:
            assert f.read() == content

    def test_generatecontent_invalid_type(self):
        # Create a user and a document to test invalid type handling
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username="u1", password="pass")
        Document = models_mod.Document
        doc = Document.objects.create(user=user, filename="f.txt", filepath="uploads/f.txt", fileType="txt", size=1)

        self.client.force_authenticate(user=user)

        url = f"/api/documents/{doc.id}/generate/"
        resp = self.client.post(url, data={"type": "invalid"}, format="json")

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_generatecontent_not_found_and_no_notes(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username="u2", password="pass")
        self.client.force_authenticate(user=user)

        # Non-existent document id
        url = f"/api/documents/9999/generate/"
        resp = self.client.post(url, data={"type": "summary"}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

        # Create a document without notes and try to generate summary -> 400
        Document = models_mod.Document
        doc = Document.objects.create(user=user, filename="f2.txt", filepath="uploads/f2.txt", fileType="txt", size=1)
        url = f"/api/documents/{doc.id}/generate/"
        resp2 = self.client.post(url, data={"type": "summary"}, format="json")
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST

    @patch('core.views.generate_summary_from_notes')
    @patch('core.views.generate_quiz_from_notes')
    def test_generatecontent_triggers_tasks(self, mock_quiz_task, mock_summary_task):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username="u3", password="pass")
        self.client.force_authenticate(user=user)

        Document = models_mod.Document
        GeneratedContent = models_mod.GeneratedContent

        doc = Document.objects.create(user=user, filename="f3.txt", filepath="uploads/f3.txt", fileType="txt", size=1)
        # create notes so generation can proceed
        GeneratedContent.objects.create(document=doc, contentType="notes", contentData={"markdown_text": "abc"})

        url = f"/api/documents/{doc.id}/generate/"
        # summary
        resp = self.client.post(url, data={"type": "summary"}, format="json")
        assert resp.status_code == status.HTTP_202_ACCEPTED
        mock_summary_task.delay.assert_called()

        # quiz
        resp2 = self.client.post(url, data={"type": "quiz"}, format="json")
        assert resp2.status_code == status.HTTP_202_ACCEPTED
        mock_quiz_task.delay.assert_called()
