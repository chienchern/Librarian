import os
from typing import Optional


def get_api_key(key_name: str) -> Optional[str]:
    """Get API key from environment variables."""
    return os.getenv(key_name)


def get_google_books_api_key() -> Optional[str]:
    """Get Google Books API key."""
    return get_api_key("GOOGLE_BOOKS_API_KEY")


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key."""
    return get_api_key("GEMINI_API_KEY")


def get_exa_api_key() -> Optional[str]:
    """Get Exa API key."""
    return get_api_key("EXA_API_KEY")


def get_tavily_api_key() -> Optional[str]:
    """Get Tavily API key."""
    return get_api_key("TAVILY_API_KEY")