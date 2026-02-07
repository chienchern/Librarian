"""Tests for all Pydantic models across the application."""

import pytest
from pydantic import ValidationError

from librarian.analysis.models import BookDNAResponse, DNAPillar, DNASettingPillar, BookDNA
from librarian.ranking.models import (
    CandidateBook,
    CandidateList,
    RankedCandidate,
    RankedCandidateOutput,
    RankingOutput,
    RankingResponse,
)
from librarian.writing.models import (
    LLMRecommendation,
    RecommendationCard,
    RecommendationOutput,
    RecommendationResponse,
)
from librarian.seed.models import ParsedBookQuery
from librarian.shared.models.book_metadata import BookMetadata

from helpers import make_book_dna, make_dna_pillar, make_setting_pillar


# ---------------------------------------------------------------------------
# ParsedBookQuery
# ---------------------------------------------------------------------------

class TestParsedBookQuery:
    def test_to_google_query_title_only(self):
        q = ParsedBookQuery(title="The Martian")
        assert q.to_google_query() == 'intitle:"The Martian"'

    def test_to_google_query_author_only(self):
        q = ParsedBookQuery(author="Andy Weir")
        assert q.to_google_query() == 'inauthor:"Andy Weir"'

    def test_to_google_query_both(self):
        q = ParsedBookQuery(title="The Martian", author="Andy Weir")
        result = q.to_google_query()
        assert 'intitle:"The Martian"' in result
        assert 'inauthor:"Andy Weir"' in result

    def test_to_google_query_empty(self):
        q = ParsedBookQuery()
        assert q.to_google_query() == ""

    def test_fields_default_to_none(self):
        q = ParsedBookQuery()
        assert q.title is None
        assert q.author is None

    def test_to_google_query_escapes_quotes(self):
        """Test that double quotes in title/author are stripped to avoid breaking query string."""
        q = ParsedBookQuery(title='Project "Hail" Mary', author='Andy "The Author" Weir')
        result = q.to_google_query()
        # Quotes should be removed from title and author
        assert result == 'intitle:"Project Hail Mary" inauthor:"Andy The Author Weir"'


# ---------------------------------------------------------------------------
# BookMetadata
# ---------------------------------------------------------------------------

class TestBookMetadata:
    def test_creation(self):
        m = BookMetadata(book_id="abc", title="T", author="A")
        assert m.book_id == "abc"
        assert m.blurb is None
        assert m.thumbnail is None

    def test_optional_fields(self):
        m = BookMetadata(book_id="x", title="T", author="A", blurb="B", thumbnail="http://img")
        assert m.blurb == "B"
        assert m.thumbnail == "http://img"


# ---------------------------------------------------------------------------
# DNA Pillar models
# ---------------------------------------------------------------------------

class TestDNAPillar:
    def test_creation(self):
        p = make_dna_pillar("Full description", "Summary")
        assert p.full_text == "Full description"
        assert p.summary == "Summary"

    def test_validation_error_missing_fields(self):
        with pytest.raises(ValidationError):
            DNAPillar()


class TestDNASettingPillar:
    def test_creation(self):
        s = make_setting_pillar()
        assert s.time == "Present day"
        assert s.place == "New York"
        assert s.vibe == "Gritty"

    def test_validation_error_missing_fields(self):
        with pytest.raises(ValidationError):
            DNASettingPillar()


# ---------------------------------------------------------------------------
# BookDNAResponse
# ---------------------------------------------------------------------------

class TestBookDNAResponse:
    def test_creation(self):
        dna = make_book_dna()
        assert dna.book_id == "test-book-id"
        assert dna.genre == "Literary fiction"
        assert len(dna.dealbreakers) == 4

    def test_all_pillars_present(self):
        dna = make_book_dna()
        assert dna.setting is not None
        assert dna.narrative_engine is not None
        assert dna.prose_texture is not None
        assert dna.emotional_profile is not None
        assert dna.structural_quirks is not None
        assert dna.theme is not None

    def test_serialization_roundtrip(self):
        dna = make_book_dna()
        data = dna.model_dump()
        restored = BookDNAResponse(**data)
        assert restored.book_id == dna.book_id
        assert restored.setting.time == dna.setting.time
        assert restored.dealbreakers == dna.dealbreakers

    def test_pillar_access_by_name(self):
        dna = make_book_dna()
        valid_pillars = ["setting", "narrative_engine", "prose_texture", "emotional_profile", "structural_quirks", "theme"]
        for name in valid_pillars:
            pillar = getattr(dna, name)
            assert pillar is not None
            assert hasattr(pillar, "full_text")


# ---------------------------------------------------------------------------
# Candidate models
# ---------------------------------------------------------------------------

class TestCandidateBook:
    def test_creation(self):
        c = CandidateBook(title="T", author="A", source_snippet="S")
        assert c.title == "T"

    def test_validation_error(self):
        with pytest.raises(ValidationError):
            CandidateBook()


class TestCandidateList:
    def test_creation(self):
        cl = CandidateList(candidates=[CandidateBook(title="T", author="A", source_snippet="S")])
        assert len(cl.candidates) == 1

    def test_empty_list(self):
        cl = CandidateList(candidates=[])
        assert len(cl.candidates) == 0

    def test_serialization_roundtrip(self):
        cl = CandidateList(candidates=[CandidateBook(title="T", author="A", source_snippet="S")])
        data = cl.model_dump()
        restored = CandidateList(**data)
        assert restored.candidates[0].title == "T"


# ---------------------------------------------------------------------------
# Ranking models
# ---------------------------------------------------------------------------

class TestRankingModels:
    def test_ranked_candidate_output(self):
        r = RankedCandidateOutput(title="T", author="A", rank=1, confidence_score=85.0, reasoning="Good")
        assert r.rank == 1

    def test_ranking_output(self):
        ro = RankingOutput(candidates=[
            RankedCandidateOutput(title="T", author="A", rank=1, confidence_score=85.0, reasoning="Good")
        ])
        assert len(ro.candidates) == 1

    def test_ranked_candidate_with_dna(self):
        dna = make_book_dna()
        rc = RankedCandidate(title="T", author="A", rank=1, confidence_score=85.0, reasoning="Good", dna=dna)
        assert rc.dna is not None

    def test_ranked_candidate_without_dna(self):
        rc = RankedCandidate(title="T", author="A", rank=1, confidence_score=85.0, reasoning="Good", dna=None)
        assert rc.dna is None

    def test_ranking_response(self):
        rr = RankingResponse(candidates=[], total_analyzed=0, failed_analyses=3)
        assert rr.failed_analyses == 3


# ---------------------------------------------------------------------------
# Recommendation models
# ---------------------------------------------------------------------------

class TestRecommendationModels:
    def test_llm_recommendation(self):
        r = LLMRecommendation(
            title="T", author="A", rank=1, confidence_score=90.0,
            why_it_matches="Because X", what_is_fresh="Fresh Y"
        )
        assert r.why_it_matches == "Because X"

    def test_recommendation_output(self):
        ro = RecommendationOutput(recommendations=[
            LLMRecommendation(
                title="T", author="A", rank=1, confidence_score=90.0,
                why_it_matches="W", what_is_fresh="F"
            )
        ])
        assert len(ro.recommendations) == 1

    def test_recommendation_card(self):
        rc = RecommendationCard(
            title="T", author="A", rank=1, confidence_score=90.0,
            why_it_matches="W", what_is_fresh="F", dna=None
        )
        assert rc.dna is None

    def test_recommendation_response(self):
        rr = RecommendationResponse(recommendations=[], total_analyzed=3, failed_analyses=1)
        assert rr.total_analyzed == 3
