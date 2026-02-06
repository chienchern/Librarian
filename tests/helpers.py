"""Shared test helpers and factory functions."""

from unittest.mock import AsyncMock, MagicMock

from librarian.analysis.models import BookDNAResponse, DNAPillar, DNASettingPillar
from librarian.ranking.models import (
    CandidateBook,
    CandidateList,
    RankedCandidate,
    RankingResponse,
)
from librarian.writing.models import RecommendationCard, RecommendationResponse
from librarian.seed.models import ParsedBookQuery
from librarian.shared.models.book_metadata import BookMetadata


# ---------------------------------------------------------------------------
# Reusable factory helpers
# ---------------------------------------------------------------------------

def make_dna_pillar(full_text: str = "Test pillar", summary: str = "Test") -> DNAPillar:
    return DNAPillar(full_text=full_text, summary=summary)


def make_setting_pillar(
    time: str = "Present day",
    place: str = "New York",
    vibe: str = "Gritty",
    full_text: str = "Present day New York, gritty atmosphere",
    summary: str = "Gritty NYC",
) -> DNASettingPillar:
    return DNASettingPillar(time=time, place=place, vibe=vibe, full_text=full_text, summary=summary)


def make_book_dna(
    book_id: str = "test-book-id",
    title: str = "Test Book",
    genre: str = "Literary fiction",
) -> BookDNAResponse:
    return BookDNAResponse(
        book_id=book_id,
        title=title,
        genre=genre,
        setting=make_setting_pillar(),
        narrative_engine=make_dna_pillar("Character-driven narrative", "Character-driven"),
        prose_texture=make_dna_pillar("Sparse, precise prose", "Sparse prose"),
        emotional_profile=make_dna_pillar("Melancholy with hope", "Melancholy hopeful"),
        structural_quirks=make_dna_pillar("Linear timeline", "Linear"),
        theme=make_dna_pillar("Identity and belonging", "Identity"),
        dealbreakers=["Love triangles", "Chosen one trope", "Info dumps", "Deus ex machina"],
    )


def make_candidate_book(
    title: str = "Candidate Book",
    author: str = "Candidate Author",
    source_snippet: str = "Great match for prose style",
) -> CandidateBook:
    return CandidateBook(title=title, author=author, source_snippet=source_snippet)


def make_candidate_list(n: int = 3) -> CandidateList:
    candidates = [
        make_candidate_book(title=f"Book {i}", author=f"Author {i}", source_snippet=f"Match reason {i}")
        for i in range(1, n + 1)
    ]
    return CandidateList(candidates=candidates)


def make_ranked_candidate(
    title: str = "Ranked Book",
    author: str = "Ranked Author",
    rank: int = 1,
    confidence_score: float = 85.0,
    reasoning: str = "Strong pillar match",
    dna: BookDNAResponse | None = None,
) -> RankedCandidate:
    return RankedCandidate(
        title=title,
        author=author,
        rank=rank,
        confidence_score=confidence_score,
        reasoning=reasoning,
        dna=dna or make_book_dna(title=title),
    )


def make_ranking_response(n: int = 3) -> RankingResponse:
    candidates = [
        make_ranked_candidate(
            title=f"Ranked Book {i}",
            author=f"Author {i}",
            rank=i,
            confidence_score=90.0 - i * 5,
        )
        for i in range(1, n + 1)
    ]
    return RankingResponse(candidates=candidates, total_analyzed=n, failed_analyses=0)


def make_book_metadata(
    book_id: str = "google-id-123",
    title: str = "The Great Novel",
    author: str = "Jane Author",
    blurb: str = "A compelling story about life and love.",
    thumbnail: str = "https://books.google.com/thumbnail.jpg",
) -> BookMetadata:
    return BookMetadata(
        book_id=book_id, title=title, author=author, blurb=blurb, thumbnail=thumbnail
    )


# ---------------------------------------------------------------------------
# Mock helpers for Strands Agent
# ---------------------------------------------------------------------------

class FakeAgentResult:
    """Mimics the AgentResult returned by Agent.__call__ / invoke_async."""

    def __init__(self, structured_output):
        self.structured_output = structured_output


def make_mock_agent(structured_output=None):
    """Create a mock Agent whose invoke_async returns a FakeAgentResult."""
    agent = MagicMock()
    agent.invoke_async = AsyncMock(return_value=FakeAgentResult(structured_output))
    return agent
