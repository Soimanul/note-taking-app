import os
from abc import ABC, abstractmethod
import json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import pinecone


# ==============================================================================
#  1. Adapter Pattern for Generative AI Services
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

    def generate_notes(self, text: str) -> str:
        """
        Uses a detailed prompt to transform raw text into well-structured
        educational notes in Markdown format.
        """
        if not self.model:
            raise ConnectionError("Gemini model is not initialized.")

        prompt = f"""
        You are an expert AI note-taking assistant for high-level material. 
        Your task is to take the following raw text from a document and transform it into clear, concise, and well-organized notes formatted in Markdown.

        Please adhere to the following structure and guidelines:
        1.  **Organize Content:** Create a logical structure with main topics and subtopics using Markdown headings (#, ##, ###).
        2.  **Improve Readability:** Use bullet points, numbered lists, and indentation.
        3.  **Highlight Key Information:** Emphasize key concepts, definitions, and important facts in **bold**.
        4.  **Simplify:** Create brief, easy-to-understand explanations for complex ideas.
        5.  **Engage:** Generate a few thought-provoking questions related to the material to stimulate critical thinking.
        6.  **Suggest Examples:** Propose relevant real-world examples or applications of the concepts.
        7.  **Identify Gaps:** Flag any areas that seem unclear or may require further research.
        8.  **Provide a Glossary:** At the end, create a 'Glossary' section for new terms introduced in the text.
        9.  **Main Takeaways:** Conclude with a 'Main Takeaways' section summarizing the most critical points.

        Here is the document text:
        ---
        {text}
        ---
        """
        response = self.model.generate_content(prompt)
        return response.text

    def generate_summary(self, text: str) -> str:
        """Takes existing text (like notes) and generates a simple summary."""
        if not self.model:
            raise ConnectionError("Gemini model is not initialized.")
        prompt = f"Please provide a concise, one-paragraph summary of the following notes:\n\n{text}"
        response = self.model.generate_content(prompt)
        return response.text

    def generate_quiz(self, text: str) -> dict:
        """
        Uses a detailed prompt to generate a quiz with multiple choice and
        fill-in-the-blank questions, returning a structured JSON object.
        """
        if not self.model:
            raise ConnectionError("Gemini model is not initialized.")

        prompt = f"""
        You are an AI designed to create educational quizzes. Based on the following notes, generate a quiz in a valid JSON format.

        The JSON object must have two top-level keys: "multiple_choice" and "fill_in_the_blanks".

        1.  **"multiple_choice"**: This should be a list containing exactly 20 question objects. Each object must have three keys:
            - "question": A string containing the question text.
            - "options": A list of exactly 4 strings representing the possible answers.
            - "correct_answer_index": An integer (0, 1, 2, or 3) indicating the index of the correct answer in the "options" list.

        2.  **"fill_in_the_blanks"**: This should be a list containing exactly 5 question objects. Each object must have two keys:
            - "question": A string containing a sentence with a blank space indicated by "____".
            - "answer": A string containing the correct word or phrase that fills the blank.

        Here are the notes to base the quiz on:
        ---
        {text}
        ---
        """

        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        response = self.model.generate_content(
            prompt, generation_config=generation_config
        )

        return json.loads(response.text)


# ==============================================================================
#  2. Service Instantiation
# ==============================================================================

ai_adapter: GenerativeAIAdapter = GeminiAdapter()

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
    print(f"Error initializing services: {e}")
    embedding_model = None
    pinecone_index = None
