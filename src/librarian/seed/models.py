from pydantic import BaseModel, Field


class ParsedBookQuery(BaseModel):
    """Structured book search query."""
    title: str | None = Field(None, description="Book title or partial title")
    author: str | None = Field(None, description="Author name or partial name")
    
    def to_google_query(self) -> str:
        """Convert to Google Books API query string."""
        parts = []
        if self.title:
            # Strip/escape double quotes to avoid breaking the query string
            safe_title = self.title.strip().replace('"', '')
            parts.append(f'intitle:"{safe_title}"')
        if self.author:
            # Strip/escape double quotes to avoid breaking the query string
            safe_author = self.author.strip().replace('"', '')
            parts.append(f'inauthor:"{safe_author}"')
        return " ".join(parts) if parts else ""