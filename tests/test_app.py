"""Tests for FastAPI application endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient

from helpers import (
    make_book_dna,
    make_book_metadata,
    make_candidate_list,
    make_ranking_response,
)
from librarian.ranking.models import CandidateList, CandidateBook
from librarian.writing.models import (
    RecommendationCard,
    RecommendationResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def app_with_mocks():
    """Create the FastAPI app with all globals mocked."""
    import librarian.app as app_module

    # Mock the global instances
    mock_books_api = MagicMock()
    mock_books_api.close = AsyncMock()
    mock_book_analyzer = MagicMock()
    mock_candidates_finder = MagicMock()
    mock_book_ranker = MagicMock()
    mock_recommendations_writer = MagicMock()

    app_module.books_api = mock_books_api
    app_module.book_analyzer = mock_book_analyzer
    app_module.candidates_finder = mock_candidates_finder
    app_module.book_ranker = mock_book_ranker
    app_module.recommendations_writer = mock_recommendations_writer

    return {
        "app": app_module.app,
        "books_api": mock_books_api,
        "book_analyzer": mock_book_analyzer,
        "candidates_finder": mock_candidates_finder,
        "book_ranker": mock_book_ranker,
        "recommendations_writer": mock_recommendations_writer,
    }


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

class TestHomePage:
    @pytest.mark.asyncio
    async def test_home_returns_200(self, app_with_mocks):
        app = app_with_mocks["app"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# API: Book search
# ---------------------------------------------------------------------------

class TestAPISearch:
    @pytest.mark.asyncio
    async def test_search_returns_books(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        mocks["books_api"].search = AsyncMock(return_value=[
            make_book_metadata(book_id="b1", title="Book 1"),
            make_book_metadata(book_id="b2", title="Book 2"),
        ])

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/books/search?q=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Book 1"

    @pytest.mark.asyncio
    async def test_search_requires_query(self, app_with_mocks):
        app = app_with_mocks["app"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/books/search")
        assert response.status_code == 422  # Validation error


# ---------------------------------------------------------------------------
# API: Get book
# ---------------------------------------------------------------------------

class TestAPIGetBook:
    @pytest.mark.asyncio
    async def test_get_book_found(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        mocks["books_api"].get_book = AsyncMock(return_value=make_book_metadata())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/books/google-id-123")

        assert response.status_code == 200
        assert response.json()["title"] == "The Great Novel"


# ---------------------------------------------------------------------------
# API: Analyze book
# ---------------------------------------------------------------------------

class TestAPIAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_success(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        mocks["books_api"].get_book = AsyncMock(return_value=make_book_metadata())
        fake_dna = make_book_dna()
        mocks["book_analyzer"].analyze = AsyncMock(return_value=fake_dna)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/books/book-1/analyze")

        assert response.status_code == 200
        data = response.json()
        assert data["genre"] == "Literary fiction"

    @pytest.mark.asyncio
    async def test_analyze_book_not_found(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        mocks["books_api"].get_book = AsyncMock(return_value=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/books/nonexistent/analyze")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_analyze_failure(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        mocks["books_api"].get_book = AsyncMock(return_value=make_book_metadata())
        mocks["book_analyzer"].analyze = AsyncMock(return_value=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/books/book-1/analyze")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# API: Find candidates
# ---------------------------------------------------------------------------

class TestAPIFindCandidates:
    @pytest.mark.asyncio
    async def test_find_candidates_success(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        fake_candidates = make_candidate_list(n=3)
        mocks["candidates_finder"].find_candidates = AsyncMock(return_value=fake_candidates)

        dna = make_book_dna()
        request_body = {
            "selected_pillars": ["prose_texture", "theme"],
            "dealbreakers": ["Love triangles"],
            "dna": dna.model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/find-candidates", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert len(data["candidates"]) == 3

    @pytest.mark.asyncio
    async def test_find_candidates_no_pillars(self, app_with_mocks):
        app = app_with_mocks["app"]

        request_body = {
            "selected_pillars": [],
            "dealbreakers": [],
            "dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/find-candidates", json=request_body)

        assert response.status_code == 400
        assert "At least one pillar" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_find_candidates_too_many_pillars(self, app_with_mocks):
        app = app_with_mocks["app"]

        request_body = {
            "selected_pillars": ["prose_texture", "theme", "setting", "narrative_engine"],
            "dealbreakers": [],
            "dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/find-candidates", json=request_body)

        assert response.status_code == 400
        assert "Maximum 3" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_find_candidates_invalid_pillar(self, app_with_mocks):
        app = app_with_mocks["app"]

        request_body = {
            "selected_pillars": ["invalid_pillar"],
            "dealbreakers": [],
            "dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/find-candidates", json=request_body)

        assert response.status_code == 400
        assert "Invalid pillars" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_find_candidates_no_dna(self, app_with_mocks):
        app = app_with_mocks["app"]

        request_body = {
            "selected_pillars": ["theme"],
            "dealbreakers": [],
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/find-candidates", json=request_body)

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# API: Rank candidates
# ---------------------------------------------------------------------------

class TestAPIRankCandidates:
    @pytest.mark.asyncio
    async def test_rank_candidates_success(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        ranking = make_ranking_response(n=2)
        mocks["book_ranker"].rank_candidates = AsyncMock(return_value=ranking)

        request_body = {
            "candidates": [c.model_dump() for c in make_candidate_list(n=2).candidates],
            "selected_pillars": ["theme"],
            "dealbreakers": [],
            "seed_dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/rank-candidates", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert len(data["candidates"]) == 2

    @pytest.mark.asyncio
    async def test_rank_candidates_missing_data(self, app_with_mocks):
        app = app_with_mocks["app"]

        request_body = {
            "candidates": [],
            "selected_pillars": ["theme"],
            "seed_dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/rank-candidates", json=request_body)

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# API: Write recommendations
# ---------------------------------------------------------------------------

class TestAPIWriteRecommendations:
    @pytest.mark.asyncio
    async def test_write_recommendations_success(self, app_with_mocks):
        app = app_with_mocks["app"]
        mocks = app_with_mocks

        fake_response = RecommendationResponse(
            recommendations=[
                RecommendationCard(
                    title="Rec 1", author="Auth 1", rank=1, confidence_score=90.0,
                    why_it_matches="Because X", what_is_fresh="Fresh Y", dna=None
                ),
            ],
            total_analyzed=1,
            failed_analyses=0,
        )
        mocks["recommendations_writer"].write_recommendations = AsyncMock(return_value=fake_response)

        request_body = {
            "ranking": make_ranking_response(n=1).model_dump(),
            "selected_pillars": ["theme"],
            "dealbreakers": [],
            "seed_dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/write-recommendations", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["why_it_matches"] == "Because X"

    @pytest.mark.asyncio
    async def test_write_recommendations_missing_ranking(self, app_with_mocks):
        app = app_with_mocks["app"]

        request_body = {
            "selected_pillars": ["theme"],
            "seed_dna": make_book_dna().model_dump(),
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/books/book-1/write-recommendations", json=request_body)

        assert response.status_code == 400
