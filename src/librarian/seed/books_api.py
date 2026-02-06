import logging
import httpx
from langdetect import detect, LangDetectException
from .query_parser import QueryParser
from .models import ParsedBookQuery
from ..shared.models.book_metadata import BookMetadata
from ..shared.config.api_keys import get_google_books_api_key

logger = logging.getLogger("librarian")


class BooksAPI:
    """Google Books API client with LLM-powered query parsing."""
    
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    def __init__(self, use_llm_parser: bool = True):
        self.api_key = get_google_books_api_key()
        self.client = httpx.AsyncClient(timeout=10.0)
        self.query_parser = QueryParser() if use_llm_parser else None
    
    async def search(self, query: str, max_results: int = 10) -> list[BookMetadata]:
        """Search for books by query string.
        
        Uses LLM to parse ambiguous queries into structured title/author fields.
        """
        # Major step logging
        logger.info("BOOK SEARCH", extra={'step': True})
        logger.info(f"Raw search query: {query!r}", extra={'query': True})
        
        # Try LLM parsing first
        search_query = query
        if self.query_parser:
            try:
                parsed = await self.query_parser.parse(query)
                logger.info(f"LLM parsed - title: {parsed.title!r}, author: {parsed.author!r}", extra={'response': True})
                structured_query = parsed.to_google_query()
                if structured_query:
                    search_query = structured_query
            except Exception as e:
                logger.warning(f"LLM Parser Failed: {e}, falling back to raw query")
        
        logger.info(f"Final Google Books query: {search_query!r}", extra={'query': True})
        
        params = {"q": search_query, "maxResults": max_results * 2, "langRestrict": "en"}
        if self.api_key:
            params["key"] = self.api_key
        
        logger.info(f"Google Books API request: GET {self.BASE_URL} with params: {params}", extra={'query': True})
        
        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Google Books raw response: {len(data.get('items', []))} items", extra={'response': True})
        
        books = []
        seen_books = set()
        filtered_count = 0
        
        for item in data.get("items", []):
            book = self._parse_book(item)
            if book:  # None means filtered out
                # Dedupe by title + author (case-insensitive)
                book_key = (book.title.lower(), book.author.lower())
                if book_key not in seen_books:
                    seen_books.add(book_key)
                    books.append(book)
                    if len(books) >= max_results:
                        break
            else:
                filtered_count += 1
        
        logger.info(f"Final results: {len(books)} books (filtered out {filtered_count})", extra={'response': True})
        return books
    
    def _parse_book(self, item: dict) -> BookMetadata | None:
        """Parse a Google Books API item into BookMetadata.
        
        Returns None if the book should be filtered out (no cover, non-English description).
        """
        info = item.get("volumeInfo", {})
        
        # Filter books without covers
        thumbnail = info.get("imageLinks", {}).get("thumbnail")
        if not thumbnail:
            return None
        
        blurb = info.get("description")
        
        # Filter non-English books using langdetect on description
        if blurb:
            try:
                if detect(blurb) != "en":
                    return None
            except LangDetectException as e:
                logger.warning(f"langdetect failed for '{info.get('title', 'Unknown')}': {e}")
                return None  # Filter out if detection fails
        else:
            return None  # Filter out books without descriptions
            
        return BookMetadata(
            book_id=item["id"],
            title=info.get("title", "Unknown"),
            author=", ".join(info.get("authors", ["Unknown"])),
            blurb=blurb,
            thumbnail=thumbnail,
        )
    
    async def get_book(self, book_id: str) -> BookMetadata | None:
        """Get a specific book by ID."""
        url = f"{self.BASE_URL}/{book_id}"
        params = {"key": self.api_key} if self.api_key else {}
        
        response = await self.client.get(url, params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        
        return self._parse_book(response.json())
    
    async def close(self):
        await self.client.aclose()