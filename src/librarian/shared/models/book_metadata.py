from pydantic import BaseModel


class BookMetadata(BaseModel):
    """Book metadata from Google Books API."""
    book_id: str
    title: str
    author: str
    blurb: str | None = None
    thumbnail: str | None = None