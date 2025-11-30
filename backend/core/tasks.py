import os
import tempfile
from abc import ABC, abstractmethod
from celery import shared_task
import fitz
import docx
from .models import Document, GeneratedContent, Log
from . import services


# ==============================================================================
#  1. Strategy Pattern for file parsing
# ==============================================================================
class ParserStrategy(ABC):
    """
    Abstract base class for all file parser strategies.
    """

    @abstractmethod
    def parse(self, filepath: str) -> str:
        """
        Reads a file and returns its text content.
        """

        pass


class PdfParser(ParserStrategy):
    """
    Strategy for parsing '.pdf' files using PyMuPDF.
    """

    def parse(self, filepath: str) -> str:
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text() + "\n"
        return text


class DocxParser(ParserStrategy):
    """
    Strategy for parsing '.docx' files.
    """

    def parse(self, filepath: str) -> str:
        text = ""
        doc = docx.Document(filepath)  # pylint: disable=no-member
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text


class TextParser(ParserStrategy):
    """
    Strategy for parsing plain text ('.txt', '.md') files.
    """

    def parse(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()


PARSER_STRATEGIES = {
    "pdf": PdfParser(),
    "docx": DocxParser(),
    "txt": TextParser(),
    "md": TextParser(),
}


def get_parser(filetype: str) -> ParserStrategy:
    """
    Factory function to select the appropriate parser strategy.
    """

    parser = PARSER_STRATEGIES.get(filetype.lower())
    if not parser:
        raise ValueError(f"Unsupported file type: {filetype}")
    return parser


# ==============================================================================
#  2. Helper Functions for the Main Task
# ==============================================================================
def _generate_and_save_notes(document: Document, text: str):
    """Generates structured notes and saves them to the database."""
    print("Generating structured notes...")
    notes_text = services.ai_adapter.generate_notes(text)
    GeneratedContent.objects.create(
        document=document,
        contentType="notes",
        contentData={"markdown_text": notes_text},
    )
    print("Notes generated and saved.")


def _generate_and_upsert_embedding(document: Document, text: str):
    """Generates an embedding and upserts it to Pinecone."""
    print("Generating embeddings...")
    embedding = services.embedding_model.encode(text).tolist()
    print(f"Embedding generated with dimension: {len(embedding)}")

    print("Upserting vector to Pinecone...")
    services.pinecone_index.upsert(
        vectors=[
            {
                "id": str(document.id),
                "values": embedding,
                "metadata": {"user_id": str(document.user.id)},
            }
        ]
    )
    print("Vector upserted successfully.")


# ==============================================================================
#  3. Main Celery Task for Document Processing
# ==============================================================================
@shared_task
def process_document(document_id):
    """
    Orchestrates the initial document processing workflow:
    1. Parses text.
    2. Generates structured notes.
    3. Creates and stores an embedding.
    """
    # Initialize ML services lazily (only when task runs)
    services.initialize_ml_services()
    
    if not all(
        [services.ai_adapter, services.embedding_model, services.pinecone_index]
    ):
        raise ConnectionError("AI services are not initialized.")

    try:
        doc = Document.objects.get(id=document_id)
        
        print(f"Processing document: {doc.filename} (ID: {document_id})")
        print(f"File path: {doc.filepath}")

        # File is directly accessible on mounted Azure Files volume
        # No need for temporary files - parse directly from mounted storage
        filepath = doc.filepath.path  # e.g., /app/media/uploads/file.pdf
        print(f"Reading file from: {filepath}")
        
        parser = get_parser(doc.fileType)
        extracted_text = parser.parse(filepath)
        print(
            f"File parsed successfully. Text length: {len(extracted_text)} characters."
        )

        _generate_and_save_notes(doc, extracted_text)
        _generate_and_upsert_embedding(doc, extracted_text)

        doc.status = "completed"
        doc.save()
        Log.objects.create(
            user=doc.user,
            document=doc,
            level="INFO",
            message=f'Document "{doc.filename}" processed successfully.',
        )
        print("Document status updated to 'completed'.")

    except Document.DoesNotExist:
        print(f"Document with id={document_id} not found.")
    except Exception as e:
        doc, _ = Document.objects.update_or_create(
            id=document_id, defaults={"status": "failed"}
        )
        Log.objects.create(
            user=doc.user,
            document=doc,
            level="ERROR",
            message=f'Processing failed for "{doc.filename}": {str(e)}',
        )
        print(f"Processing failed for document {document_id}: {str(e)}")


# ==============================================================================
#  4. On-Demand Celery Tasks
# ==============================================================================
@shared_task
def generate_summary_from_notes(document_id):
    """
    Takes the existing 'notes' for a document and generates a new 'summary' object.
    """
    try:
        # Get the original doc and its notes
        doc = Document.objects.get(id=document_id)
        notes_content = GeneratedContent.objects.get(document=doc, contentType="notes")
        notes_text = notes_content.contentData.get("markdown_text", "")

        if not notes_text:
            raise ValueError("Could not find notes to summarize.")

        # Call the AI adapter to generate the summary
        print(f"Generating summary for document: {doc.filename}")
        summary_text = services.ai_adapter.generate_summary(notes_text)

        # Create a new GeneratedContent object for the summary
        GeneratedContent.objects.create(
            document=doc,
            contentType="summary",
            contentData={"markdown_text": summary_text},
        )
        print("New summary object created successfully.")
        Log.objects.create(
            user=doc.user,
            document=doc,
            level="INFO",
            message="Summary generated successfully.",
        )

    except (Document.DoesNotExist, GeneratedContent.DoesNotExist):
        print(f"Could not find document or notes for document_id: {document_id}")
    except Exception as e:
        print(f"Failed to generate summary for document {document_id}: {str(e)}")
        doc, _ = Document.objects.update_or_create(id=document_id, defaults={})
        Log.objects.create(
            user=doc.user,
            document=doc,
            level="ERROR",
            message=f"Summary generation failed: {str(e)}",
        )


@shared_task
def generate_quiz_from_notes(document_id):
    """
    Takes existing notes for a document and generates a new quiz object.
    """
    try:
        # Get the original doc and its notes
        doc = Document.objects.get(id=document_id)
        notes_content = GeneratedContent.objects.get(document=doc, contentType="notes")
        notes_text = notes_content.contentData.get("markdown_text", "")

        if not notes_text:
            raise ValueError("Could not find notes to generate quiz from.")

        print(f"Generating quiz for document: {doc.filename}")
        quiz_data = services.ai_adapter.generate_quiz(notes_text)

        # Create a new GenerateddContent for the quiz
        GeneratedContent.objects.create(
            document=doc, contentType="quiz", contentData=quiz_data
        )
        print("New quiz object created successfully.")
        Log.objects.create(
            user=doc.user,
            document=doc,
            level="INFO",
            message="Quiz generated successfully.",
        )

    except (Document.DoesNotExist, GeneratedContent.DoesNotExist):
        print(f"Could not find document or notes for document_id: {document_id}")
    except Exception as e:
        print(f"Failed to generate quiz for document {document_id}: {str(e)}")
        doc, _ = Document.objects.update_or_create(id=document_id, defaults={})
        Log.objects.create(
            user=doc.user,
            document=doc,
            level="ERROR",
            message=f"Quiz generation failed: {str(e)}",
        )
