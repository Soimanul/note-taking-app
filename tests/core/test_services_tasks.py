import importlib
from unittest.mock import MagicMock

from core import services, tasks, models


def test_gemini_adapter_connection_error():
    # Create a GeminiAdapter-like instance with no model to force ConnectionError
    class Dummy(services.GeminiAdapter):
        def __init__(self):
            self.model = None

    adapter = Dummy()
    try:
        # calling generate_summary should raise ConnectionError when model is None
        try:
            adapter.generate_summary("text")
            assert False, "Expected ConnectionError"
        except ConnectionError:
            pass
    finally:
        pass


def test_gemini_adapter_success_paths():
    # Fake model that returns a simple object with .text
    class FakeModel:
        def generate_content(self, *args, **kwargs):
            class R:
                text = "ok"

            return R()

    class Dummy(services.GeminiAdapter):
        def __init__(self):
            self.model = FakeModel()

    adapter = Dummy()
    assert adapter.generate_summary("x") == "ok"
    assert adapter.generate_notes("x") == "ok"


def test_generate_and_upsert_embedding(db, monkeypatch):
    # create minimal user and document
    User = importlib.import_module("django.contrib.auth").get_user_model()
    user = User.objects.create_user(username="embuser", password="pass")
    Document = models.Document
    doc = Document.objects.create(user=user, filename="f.txt", filepath="uploads/f.txt", fileType="txt", size=1)

    # Mock embedding model and pinecone index
    fake_encode = MagicMock()
    fake_encode.return_value.tolist.return_value = [0.1, 0.2, 0.3]

    monkeypatch.setattr(services, "embedding_model", MagicMock(encode=fake_encode))
    mock_index = MagicMock()
    monkeypatch.setattr(services, "pinecone_index", mock_index)

    # Call helper
    tasks._generate_and_upsert_embedding(doc, "some text")

    mock_index.upsert.assert_called_once()


def test_generate_summary_and_quiz_from_notes(db, monkeypatch):
    User = importlib.import_module("django.contrib.auth").get_user_model()
    user = User.objects.create_user(username="u_summary", password="pass")
    Document = models.Document
    GeneratedContent = models.GeneratedContent
    Log = models.Log

    doc = Document.objects.create(user=user, filename="f4.txt", filepath="uploads/f4.txt", fileType="txt", size=1)
    GeneratedContent.objects.create(document=doc, contentType="notes", contentData={"markdown_text": "abc"})

    # Mock ai_adapter
    monkeypatch.setattr(services, "ai_adapter", MagicMock())
    services.ai_adapter.generate_summary.return_value = "summary text"
    services.ai_adapter.generate_quiz.return_value = {"multiple_choice": []}

    # Run generate_summary_from_notes
    tasks.generate_summary_from_notes(doc.id)
    assert GeneratedContent.objects.filter(document=doc, contentType="summary").exists()
    assert Log.objects.filter(document=doc, level="INFO").exists()

    # Run generate_quiz_from_notes
    tasks.generate_quiz_from_notes(doc.id)
    assert GeneratedContent.objects.filter(document=doc, contentType="quiz").exists()
    assert Log.objects.filter(document=doc, level="INFO").count() >= 2
