import os
from abc import ABC, abstractmethod
from celery import shared_task
import fitz
import docx
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import pinecone
from .models import Document, GeneratedContent, Log


# ==============================================================================
#  1. Adapter Pattern for Gen AI Services
# ==============================================================================
class GenerativeAIAdapter(ABC):
    """
    Abstract interface for a generative AI service adapter.
    """

    @abstractmethod
    def generate_summary(self, text: str) -> str:
        """
        Generates a summary for the given text.
        """

        pass


class GeminiAdapter(GenerativeAIAdapter):
    """
    Adapter for the Google Gemini API.
    """

    def __init__(self):
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
            print("Gemini Adapter initialized successfully.")
        except Exception as e:
            self.model = None
            print(f"Error initializing Gemini Adapter: {e}")

    def generate_summary(self, text: str) -> str:
        if not self.model:
            raise ConnectionError("Gemini model is not initialized.")
        prompt = (
            f"Please provide a concise summary of the following document:\n\n{text}"
        )
        response = self.model.generate_content(prompt)
        return response.text


def get_ai_adapter() -> GenerativeAIAdapter:
    """
    Factory function to get the configured AI adapter.
    """

    # For now, it's hardcoded to Gemini but it could be easily expaneded to choose another api.
    return GeminiAdapter()


# ==============================================================================
#  2. Initialize other AI Clients (Embeddings & Vector DB)
# ==============================================================================
try:
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Pinecone Vector DB
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY not set.")
    pc = pinecone.Pinecone(api_key=pinecone_api_key)
    pinecone_index = pc.Index("documents")

    print("Embedding model and Pinecone client initialized successfully.")
except Exception as e:
    print(f"Error initializing AI clients: {e}")
    embedding_model = None
    pinecone_index = None


# ==============================================================================
#  3. Strategy Pattern for file parsing
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
#  4. Main Celery Task for Document Processing
# ==============================================================================
@shared_task
def process_document(document_id):
    """
    Asynchronous task to process an uploaded document, generate AI content,
    and create embeddings.
    """

    ai_adapter = get_ai_adapter()
    if not all([ai_adapter, embedding_model, pinecone_index]):
        raise ConnectionError(
            "AI services are not initialized. Check API keys and configuration."
        )

    try:
        doc = Document.objects.get(id=document_id)

        # Parse the text using the Strategy pattern
        print(f"Starting to parse file: {doc.filename}")
        parser = get_parser(doc.fileType)
        extracted_text = parser.parse(doc.filepath)
        print(
            f"File parsed successfully. Text length: {len(extracted_text)} characters."
        )

        # Generate the summary using the Adapter pattern
        print("Generating summary...")
        summary_text = ai_adapter.generate_summary(extracted_text)

        GeneratedContent.objects.create(
            document=doc,
            contentType="summary",
            contentData={"markdown_text": summary_text},
        )
        print("Summary generated and saved.")

        # Generate embeddings
        print("Generating embeddings...")
        embedding = embedding_model.encode(extracted_text).tolist()
        print(f"Embedding generated with dimension: {len(embedding)}")

        # Save them to Pinecone
        print("Upserting vector to Pinecone...")
        pinecone_index.upsert(
            vectors=[
                {
                    "id": str(doc.id),
                    "values": embedding,
                    "metadata": {"user_id": str(doc.user.id)},
                }
            ]
        )
        print("Vector upserted successfully.")

        # 5. Suuccess state
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
