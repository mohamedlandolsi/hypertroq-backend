"""Google Gemini AI service integration."""
import google.generativeai as genai
from app.core.config import settings


class GeminiService:
    """Service for interacting with Google Gemini AI."""

    def __init__(self) -> None:
        """Initialize Gemini service."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini AI."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini AI error: {str(e)}")

    async def generate_chat_response(self, messages: list[dict[str, str]]) -> str:
        """Generate chat response using Gemini AI."""
        try:
            chat = self.model.start_chat(history=[])
            
            # Convert messages to Gemini format
            for msg in messages[:-1]:
                chat.send_message(msg["content"])
            
            # Send the last message and get response
            response = chat.send_message(messages[-1]["content"])
            return response.text
        except Exception as e:
            raise Exception(f"Gemini AI chat error: {str(e)}")


# Global Gemini service instance
gemini_service = GeminiService()
