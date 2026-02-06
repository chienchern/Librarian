"""Tests for BooksAPI - book search and metadata parsing."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from librarian.seed.books_api import BooksAPI
from librarian.seed.models import ParsedBookQuery
from librarian.shared.models.book_metadata import BookMetadata


# ---------------------------------------------------------------------------
# _parse_book tests (pure logic, no mocking)
# ---------------------------------------------------------------------------

class TestParseBook:
    """Tests for the _parse_book filtering logic."""

    def _make_api(self):
        """Create BooksAPI with LLM parser disabled to avoid agent init."""
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake"}):
            return BooksAPI(use_llm_parser=False)

    def _make_item(self, title="Test", authors=None, description="A great English book.", thumbnail="http://img.jpg"):
        item = {
            "id": "vol123",
            "volumeInfo": {
                "title": title,
                "authors": authors or ["Author"],
            },
        }
        if description is not None:
            item["volumeInfo"]["description"] = description
        if thumbnail is not None:
            item["volumeInfo"]["imageLinks"] = {"thumbnail": thumbnail}
        return item

    def test_parses_valid_book(self):
        api = self._make_api()
        item = self._make_item()
        book = api._parse_book(item)
        assert book is not None
        assert book.book_id == "vol123"
        assert book.title == "Test"
        assert book.author == "Author"
        assert book.blurb == "A great English book."
        assert book.thumbnail == "http://img.jpg"

    def test_filters_book_without_thumbnail(self):
        api = self._make_api()
        item = self._make_item(thumbnail=None)
        # Remove imageLinks entirely
        item["volumeInfo"].pop("imageLinks", None)
        assert api._parse_book(item) is None

    def test_filters_book_without_description(self):
        api = self._make_api()
        item = self._make_item(description=None)
        assert api._parse_book(item) is None

    def test_joins_multiple_authors(self):
        api = self._make_api()
        item = self._make_item(authors=["Author A", "Author B"])
        book = api._parse_book(item)
        assert book is not None
        assert book.author == "Author A, Author B"

    def test_defaults_unknown_for_missing_fields(self):
        api = self._make_api()
        item = {
            "id": "vol456",
            "volumeInfo": {
                "description": "An English description.",
                "imageLinks": {"thumbnail": "http://img.jpg"},
            },
        }
        book = api._parse_book(item)
        assert book is not None
        assert book.title == "Unknown"
        assert book.author == "Unknown"


# ---------------------------------------------------------------------------
# search() tests with mocked httpx and parser
# ---------------------------------------------------------------------------

class TestBooksAPISearch:
    """Tests for the async search method."""

    @pytest.mark.asyncio
    async def test_search_without_llm_parser(self):
        """Search should work when LLM parser is disabled, using raw query."""
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake"}):
            api = BooksAPI(use_llm_parser=False)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "b1",
                    "volumeInfo": {
                        "title": "The Martian",
                        "authors": ["Andy Weir"],
                        "description": "An astronaut is stranded on Mars.",
                        "imageLinks": {"thumbnail": "http://img1.jpg"},
                    },
                }
            ]
        }

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        books = await api.search("the martian")
        assert len(books) == 1
        assert books[0].title == "The Martian"

        await api.close()

    @pytest.mark.asyncio
    async def test_search_deduplicates(self):
        """Search should deduplicate books by title+author (case insensitive)."""
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake"}):
            api = BooksAPI(use_llm_parser=False)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "b1",
                    "volumeInfo": {
                        "title": "The Martian",
                        "authors": ["Andy Weir"],
                        "description": "First edition.",
                        "imageLinks": {"thumbnail": "http://img.jpg"},
                    },
                },
                {
                    "id": "b2",
                    "volumeInfo": {
                        "title": "the martian",
                        "authors": ["andy weir"],
                        "description": "Second edition duplicate.",
                        "imageLinks": {"thumbnail": "http://img2.jpg"},
                    },
                },
            ]
        }

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        books = await api.search("martian")
        assert len(books) == 1

        await api.close()

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self):
        """Search should return at most max_results books."""
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake"}):
            api = BooksAPI(use_llm_parser=False)

        items = [
            {
                "id": f"b{i}",
                "volumeInfo": {
                    "title": f"Book {i}",
                    "authors": [f"Author {i}"],
                    "description": f"Description for book {i} in English.",
                    "imageLinks": {"thumbnail": f"http://img{i}.jpg"},
                },
            }
            for i in range(10)
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"items": items}

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        books = await api.search("books", max_results=3)
        assert len(books) == 3

        await api.close()

    @pytest.mark.asyncio
    async def test_search_with_llm_parser(self):
        """Search should use LLM parser when available and it succeeds."""
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake", "GEMINI_API_KEY": "fake"}):
            with patch("librarian.seed.books_api.QueryParser") as MockParser:
                mock_parser = MagicMock()
                mock_parser.parse = AsyncMock(
                    return_value=ParsedBookQuery(title="The Martian", author="Andy Weir")
                )
                MockParser.return_value = mock_parser
                api = BooksAPI(use_llm_parser=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"items": []}

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        await api.search("andy weir martian")

        # Verify the parser was called
        mock_parser.parse.assert_awaited_once_with("andy weir martian")

        # Verify the structured query was used (contains intitle/inauthor)
        call_args = api.client.get.call_args
        query_param = call_args[1]["params"]["q"] if "params" in call_args[1] else call_args[0][1]["q"]
        assert "intitle:" in query_param or "inauthor:" in query_param

        await api.close()

    @pytest.mark.asyncio
    async def test_search_falls_back_on_parser_error(self):
        """Search should fall back to raw query when parser raises."""
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake", "GEMINI_API_KEY": "fake"}):
            with patch("librarian.seed.books_api.QueryParser") as MockParser:
                mock_parser = MagicMock()
                mock_parser.parse = AsyncMock(side_effect=RuntimeError("LLM down"))
                MockParser.return_value = mock_parser
                api = BooksAPI(use_llm_parser=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"items": []}

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        # Should not raise
        books = await api.search("some query")
        assert books == []

        await api.close()


# ---------------------------------------------------------------------------
# get_book() tests
# ---------------------------------------------------------------------------

class TestBooksAPIGetBook:
    @pytest.mark.asyncio
    async def test_get_book_found(self):
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake"}):
            api = BooksAPI(use_llm_parser=False)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "vol1",
            "volumeInfo": {
                "title": "Found Book",
                "authors": ["Author"],
                "description": "English description here.",
                "imageLinks": {"thumbnail": "http://img.jpg"},
            },
        }

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        book = await api.get_book("vol1")
        assert book is not None
        assert book.title == "Found Book"

        await api.close()

    @pytest.mark.asyncio
    async def test_get_book_not_found(self):
        with patch.dict("os.environ", {"GOOGLE_BOOKS_API_KEY": "fake"}):
            api = BooksAPI(use_llm_parser=False)

        mock_response = MagicMock()
        mock_response.status_code = 404

        api.client = MagicMock()
        api.client.get = AsyncMock(return_value=mock_response)
        api.client.aclose = AsyncMock()

        book = await api.get_book("nonexistent")
        assert book is None

        await api.close()
