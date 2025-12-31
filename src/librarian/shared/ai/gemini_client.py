from strands.models.gemini import GeminiModel
from ..config.api_keys import get_gemini_api_key


def create_gemini_model(model_id: str = "gemini-2.5-flash", temperature: float = 0.3, max_output_tokens: int = 2048) -> GeminiModel:
    """Create a configured Gemini model instance."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    return GeminiModel(
        client_args={"api_key": api_key},
        model_id=model_id,
        params={"temperature": temperature, "max_output_tokens": max_output_tokens}
    )