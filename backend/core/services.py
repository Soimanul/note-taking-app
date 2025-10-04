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
        You are an expert AI note-taking assistant for complex and high-level material. 
        Your task is to transform the following raw text into clear, structured, and insightful notes written in **pure Markdown** compatible with BlockNote (React).

        Output Rules:
        - **Return only the Markdown content.** No explanations, commentary, or text like “Here’s the revised version.”
        - **No indentation guides, code fences around the entire response, or extra spaces before headings.**
        - **Use fenced code blocks properly** (with triple backticks and language identifiers like ` ```python `, ` ```javascript `, etc.) when the source text contains code snippets.
        - Ensure all code blocks are syntactically valid and consistently formatted.

        Formatting & Content Guidelines:
        1. **Logical Structure:** Organize the material using Markdown headings (`##`, `###`, `####`), starting with `##` for top-level sections.
        2. **Readability:** Use bullet points, numbered lists, and spacing for clarity.
        3. **Highlight Key Concepts:** Use **bold** for definitions, keywords, and essential facts.
        4. **Simplify:** Rewrite dense or technical language into concise, accessible explanations.
        5. **Questions for Reflection:** Include a section titled **"Questions for Reflection"** with 3–5 thoughtful questions.
        6. **Examples & Applications:** Provide a section titled **"Examples & Applications"** with relevant real-world or practical examples.
        7. **Further Research Needed:** Add a section listing unclear or incomplete areas.
        8. **Glossary:** Define new or important terms in a **"Glossary"** section.
        9. **Main Takeaways:** End with a **"Main Takeaways"** section summarizing key points.

        Document text:
        ---
        {text}
        ---

        """
        response = self.model.generate_content(prompt)
        return response.text

    def generate_summary(self, text: str) -> str:
        """
        Takes existing text (like notes) and generates a simple summary.
        """

        if not self.model:
            raise ConnectionError("Gemini model is not initialized.")
        prompt = f"""You are an expert summarization assistant. Read the following notes carefully and produce a clear, cohesive, and well-structured summary formatted in **Markdown**.
        Your summary must:
        - Adapt its **length, structure, and level of detail** to the size and complexity of the notes.
        - Use **multiple paragraphs** when appropriate for clarity and logical flow.
        - Optionally use **Markdown headings** (##, ###) to separate major themes or sections when the material is extensive.
        - Preserve key ideas, relationships, and conclusions while removing redundancy and minor details.
        - Use **concise, natural, and professional language**.
        - Avoid meta commentary or phrases like “Here is the summary.”

        Here are the notes to summarize:
        ---
        {text}
        ---
        """
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
        You are an AI designed to create educational quizzes. Based on the following notes, generate a quiz in **valid JSON format**.
        The JSON object must contain **three top-level keys**:  
        1. `"multiple_choice"`  
        2. `"fill_in_the_blanks"`  
        3. `"answer_key"`

        ### Structure and Rules

        #### 1. "multiple_choice"
        - Must be a **list of exactly 20 objects**.
        - Each object must contain:
        - `"question"`: A string with the question text.
        - `"options"`: A list of **exactly 4 strings** representing possible answers.
        - `"correct_answer_index"`: An integer (0–3) indicating the index of the correct answer in `"options"`.

        #### 2. "fill_in_the_blanks"
        - Must be a **list of exactly 5 objects**.
        - Each object must contain:
        - `"question"`: A string with a blank space shown as `"____"`.
        - `"answer"`: A string with the correct word or phrase that fills the blank.

        #### 3. "answer_key"
        - Must be an object containing:
        - `"multiple_choice"`: A list of the correct answers (as text, *not indices*) corresponding to each question in `"multiple_choice"`.
        - `"fill_in_the_blanks"`: A list of the correct answers (as text) corresponding to each question in `"fill_in_the_blanks"`.

        ### Output Rules
        - **Return only valid JSON** — no commentary, explanations, or additional text.
        - **Do not bold, italicize, or stylize any answers.**
        - Ensure the JSON is syntactically correct and ready for direct parsing.

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
