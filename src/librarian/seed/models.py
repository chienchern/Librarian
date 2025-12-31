from pydantic import BaseModel, Field


class ParsedBookQuery(BaseModel):
    """Structured book search query."""
    title: str | None = Field(None, description="Book title or partial title")
    author: str | None = Field(None, description="Author name or partial name")
    
    def to_google_query(self) -> str:
        """Convert to Google Books API query string."""
        parts = []
        if self.title:
            parts.append(f'intitle:"{self.title}"')
        if self.author:
            parts.append(f'inauthor:"{self.author}"')
        return " ".join(parts) if parts else ""