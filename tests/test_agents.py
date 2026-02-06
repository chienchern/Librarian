"""Tests for all agent classes with mocked Strands Agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from strands.types.exceptions import StructuredOutputException

from librarian.analysis.models import BookDNAResponse
from librarian.ranking.models import (
    CandidateList,
    CandidateBook,
    RankingOutput,
    RankedCandidateOutput,
)
from librarian.writing.models import (
    LLMRecommendation,
    RecommendationOutput,
)
from librarian.seed.models import ParsedBookQuery

from helpers import (
    FakeAgentResult,
    make_book_dna,
    make_candidate_list,
    make_mock_agent,
    make_ranking_response,
)


# ---------------------------------------------------------------------------
# QueryParser
# ---------------------------------------------------------------------------

class TestQueryParser:
    @pytest.mark.asyncio
    async def test_parse_success(self):
        with patch("librarian.seed.query_parser.create_gemini_model"):
            with patch("librarian.seed.query_parser.Agent") as MockAgent:
                mock_agent = make_mock_agent(
                    ParsedBookQuery(title="The Martian", author="Andy Weir")
                )
                MockAgent.return_value = mock_agent

                from librarian.seed.query_parser import QueryParser
                parser = QueryParser()

        result = await parser.parse("andy weir martian")
        assert result.title == "The Martian"
        assert result.author == "Andy Weir"
        mock_agent.invoke_async.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_parse_structured_output_error_falls_back(self):
        with patch("librarian.seed.query_parser.create_gemini_model"):
            with patch("librarian.seed.query_parser.Agent") as MockAgent:
                mock_agent = MagicMock()
                mock_agent.invoke_async = AsyncMock(
                    side_effect=StructuredOutputException("parse error")
                )
                MockAgent.return_value = mock_agent

                from librarian.seed.query_parser import QueryParser
                parser = QueryParser()

        result = await parser.parse("garbled query")
        assert result.title == "garbled query"
        assert result.author is None


# ---------------------------------------------------------------------------
# BookAnalyzer
# ---------------------------------------------------------------------------

class TestBookAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_success(self):
        fake_dna = make_book_dna(book_id="placeholder", title="placeholder")

        with patch("librarian.analysis.book_analyzer.create_gemini_model"):
            with patch("librarian.analysis.book_analyzer.Agent") as MockAgent:
                mock_agent = make_mock_agent(fake_dna)
                MockAgent.return_value = mock_agent

                from librarian.analysis.book_analyzer import BookAnalyzer
                analyzer = BookAnalyzer()

        result = await analyzer.analyze("Project Hail Mary", "Andy Weir", "book-123")
        assert result is not None
        assert result.book_id == "book-123"
        assert result.title == "Project Hail Mary"
        mock_agent.invoke_async.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analyze_generates_id_when_missing(self):
        fake_dna = make_book_dna()

        with patch("librarian.analysis.book_analyzer.create_gemini_model"):
            with patch("librarian.analysis.book_analyzer.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(fake_dna)

                from librarian.analysis.book_analyzer import BookAnalyzer
                analyzer = BookAnalyzer()

        result = await analyzer.analyze("Some Title", "Author")
        assert result is not None
        assert result.book_id == "candidate_some_title"

    @pytest.mark.asyncio
    async def test_analyze_returns_none_on_structured_output_error(self):
        with patch("librarian.analysis.book_analyzer.create_gemini_model"):
            with patch("librarian.analysis.book_analyzer.Agent") as MockAgent:
                mock_agent = MagicMock()
                mock_agent.invoke_async = AsyncMock(
                    side_effect=StructuredOutputException("bad output")
                )
                MockAgent.return_value = mock_agent

                from librarian.analysis.book_analyzer import BookAnalyzer
                analyzer = BookAnalyzer()

        result = await analyzer.analyze("Bad Book", "Bad Author")
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_returns_none_on_generic_error(self):
        with patch("librarian.analysis.book_analyzer.create_gemini_model"):
            with patch("librarian.analysis.book_analyzer.Agent") as MockAgent:
                mock_agent = MagicMock()
                mock_agent.invoke_async = AsyncMock(side_effect=RuntimeError("network"))
                MockAgent.return_value = mock_agent

                from librarian.analysis.book_analyzer import BookAnalyzer
                analyzer = BookAnalyzer()

        result = await analyzer.analyze("Crash Book", "Crash Author")
        assert result is None


# ---------------------------------------------------------------------------
# CandidatesFinder
# ---------------------------------------------------------------------------

class TestCandidatesFinder:
    @pytest.mark.asyncio
    async def test_find_candidates_success(self):
        fake_candidates = CandidateList(candidates=[
            CandidateBook(title=f"Book {i}", author=f"Author {i}", source_snippet=f"Match {i}")
            for i in range(1, 6)
        ])

        with patch("librarian.ranking.candidates_finder.create_gemini_model"):
            with patch("librarian.ranking.candidates_finder.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(fake_candidates)

                from librarian.ranking.candidates_finder import CandidatesFinder
                finder = CandidatesFinder()

        seed_dna = make_book_dna()
        result = await finder.find_candidates(seed_dna, ["prose_texture", "theme"], ["Love triangles"])

        assert result is not None
        # Should return top 3 even though agent returned 5
        assert len(result.candidates) == 3
        assert result.candidates[0].title == "Book 1"

    @pytest.mark.asyncio
    async def test_find_candidates_returns_none_on_error(self):
        with patch("librarian.ranking.candidates_finder.create_gemini_model"):
            with patch("librarian.ranking.candidates_finder.Agent") as MockAgent:
                mock_agent = MagicMock()
                mock_agent.invoke_async = AsyncMock(
                    side_effect=StructuredOutputException("failed")
                )
                MockAgent.return_value = mock_agent

                from librarian.ranking.candidates_finder import CandidatesFinder
                finder = CandidatesFinder()

        seed_dna = make_book_dna()
        result = await finder.find_candidates(seed_dna, ["theme"], [])
        assert result is None

    @pytest.mark.asyncio
    async def test_find_candidates_builds_correct_prompt(self):
        fake_candidates = CandidateList(candidates=[
            CandidateBook(title="B", author="A", source_snippet="S")
        ])

        with patch("librarian.ranking.candidates_finder.create_gemini_model"):
            with patch("librarian.ranking.candidates_finder.Agent") as MockAgent:
                mock_agent = make_mock_agent(fake_candidates)
                MockAgent.return_value = mock_agent

                from librarian.ranking.candidates_finder import CandidatesFinder
                finder = CandidatesFinder()

        seed_dna = make_book_dna(title="Dune")
        await finder.find_candidates(seed_dna, ["setting"], [])

        # Verify the prompt was called with content mentioning Dune
        call_args = mock_agent.invoke_async.call_args
        prompt = call_args[0][0]
        assert "Dune" in prompt


# ---------------------------------------------------------------------------
# BookRanker
# ---------------------------------------------------------------------------

class TestBookRanker:
    @pytest.mark.asyncio
    async def test_rank_candidates_success(self):
        fake_dna = make_book_dna()
        ranking_output = RankingOutput(candidates=[
            RankedCandidateOutput(title="Book 1", author="Author 1", rank=1, confidence_score=90.0, reasoning="Top match"),
            RankedCandidateOutput(title="Book 2", author="Author 2", rank=2, confidence_score=80.0, reasoning="Good match"),
        ])

        with patch("librarian.ranking.book_ranker.create_gemini_model"):
            with patch("librarian.ranking.book_ranker.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(ranking_output)

                with patch("librarian.ranking.book_ranker.BookAnalyzer") as MockAnalyzer:
                    mock_analyzer_instance = MagicMock()
                    mock_analyzer_instance.analyze = AsyncMock(return_value=fake_dna)
                    MockAnalyzer.return_value = mock_analyzer_instance

                    from librarian.ranking.book_ranker import BookRanker
                    ranker = BookRanker()

        candidates = make_candidate_list(n=2)
        seed_dna = make_book_dna()

        result = await ranker.rank_candidates(seed_dna, candidates, ["prose_texture"], ["Info dumps"])

        assert len(result.candidates) == 2
        assert result.candidates[0].rank == 1
        assert result.total_analyzed == 2
        assert result.failed_analyses == 0

    @pytest.mark.asyncio
    async def test_rank_candidates_handles_analysis_failures(self):
        """When all candidate analyses fail, should return empty ranking."""
        with patch("librarian.ranking.book_ranker.create_gemini_model"):
            with patch("librarian.ranking.book_ranker.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(None)

                with patch("librarian.ranking.book_ranker.BookAnalyzer") as MockAnalyzer:
                    mock_analyzer_instance = MagicMock()
                    mock_analyzer_instance.analyze = AsyncMock(return_value=None)
                    MockAnalyzer.return_value = mock_analyzer_instance

                    from librarian.ranking.book_ranker import BookRanker
                    ranker = BookRanker()

        candidates = make_candidate_list(n=2)
        seed_dna = make_book_dna()

        result = await ranker.rank_candidates(seed_dna, candidates, ["theme"], [])
        assert len(result.candidates) == 0
        assert result.failed_analyses == 2

    @pytest.mark.asyncio
    async def test_rank_candidates_partial_analysis_failure(self):
        """When some analyses fail, should rank only successful ones."""
        fake_dna = make_book_dna()
        ranking_output = RankingOutput(candidates=[
            RankedCandidateOutput(title="Book 1", author="Author 1", rank=1, confidence_score=90.0, reasoning="Match"),
        ])

        with patch("librarian.ranking.book_ranker.create_gemini_model"):
            with patch("librarian.ranking.book_ranker.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(ranking_output)

                with patch("librarian.ranking.book_ranker.BookAnalyzer") as MockAnalyzer:
                    mock_analyzer_instance = MagicMock()
                    # First call succeeds, second fails
                    mock_analyzer_instance.analyze = AsyncMock(side_effect=[fake_dna, None])
                    MockAnalyzer.return_value = mock_analyzer_instance

                    from librarian.ranking.book_ranker import BookRanker
                    ranker = BookRanker()

        candidates = make_candidate_list(n=2)
        seed_dna = make_book_dna()

        result = await ranker.rank_candidates(seed_dna, candidates, ["theme"], [])
        assert result.total_analyzed == 1
        assert result.failed_analyses == 1


# ---------------------------------------------------------------------------
# RecommendationsWriter
# ---------------------------------------------------------------------------

class TestRecommendationsWriter:
    @pytest.mark.asyncio
    async def test_write_recommendations_success(self):
        llm_output = RecommendationOutput(recommendations=[
            LLMRecommendation(
                title="Rec 1", author="Auth 1", rank=1, confidence_score=90.0,
                why_it_matches="Great match because X", what_is_fresh="Fresh because Y"
            ),
        ])

        with patch("librarian.writing.recommendations_writer.create_gemini_model"):
            with patch("librarian.writing.recommendations_writer.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(llm_output)

                from librarian.writing.recommendations_writer import RecommendationsWriter
                writer = RecommendationsWriter()

        seed_dna = make_book_dna()
        ranking = make_ranking_response(n=1)

        result = await writer.write_recommendations(seed_dna, ranking, ["prose_texture"], [])

        assert len(result.recommendations) == 1
        assert result.recommendations[0].why_it_matches == "Great match because X"
        assert result.recommendations[0].what_is_fresh == "Fresh because Y"
        assert result.recommendations[0].dna is None  # frontend doesn't need DNA

    @pytest.mark.asyncio
    async def test_write_recommendations_empty_ranking(self):
        """Should return empty recommendations when ranking has no candidates."""
        with patch("librarian.writing.recommendations_writer.create_gemini_model"):
            with patch("librarian.writing.recommendations_writer.Agent") as MockAgent:
                MockAgent.return_value = make_mock_agent(None)

                from librarian.writing.recommendations_writer import RecommendationsWriter
                writer = RecommendationsWriter()

        seed_dna = make_book_dna()
        from librarian.ranking.models import RankingResponse
        empty_ranking = RankingResponse(candidates=[], total_analyzed=0, failed_analyses=3)

        result = await writer.write_recommendations(seed_dna, empty_ranking, ["theme"], [])
        assert len(result.recommendations) == 0
        assert result.failed_analyses == 3

    @pytest.mark.asyncio
    async def test_write_recommendations_error_returns_empty(self):
        with patch("librarian.writing.recommendations_writer.create_gemini_model"):
            with patch("librarian.writing.recommendations_writer.Agent") as MockAgent:
                mock_agent = MagicMock()
                mock_agent.invoke_async = AsyncMock(
                    side_effect=StructuredOutputException("bad")
                )
                MockAgent.return_value = mock_agent

                from librarian.writing.recommendations_writer import RecommendationsWriter
                writer = RecommendationsWriter()

        seed_dna = make_book_dna()
        ranking = make_ranking_response(n=1)

        result = await writer.write_recommendations(seed_dna, ranking, ["theme"], [])
        assert len(result.recommendations) == 0

    def test_build_candidate_summaries_with_dna(self):
        """Test the summary template rendering with DNA data."""
        with patch("librarian.writing.recommendations_writer.create_gemini_model"):
            with patch("librarian.writing.recommendations_writer.Agent") as MockAgent:
                MockAgent.return_value = MagicMock()

                from librarian.writing.recommendations_writer import RecommendationsWriter
                writer = RecommendationsWriter()

        ranking = make_ranking_response(n=1)
        summaries = writer._build_candidate_summaries(ranking)

        assert "Ranked Book 1" in summaries
        assert "Author 1" in summaries
        assert "85.0%" in summaries  # confidence_score

    def test_build_candidate_summaries_without_dna(self):
        """Test the failed template rendering when DNA is None."""
        with patch("librarian.writing.recommendations_writer.create_gemini_model"):
            with patch("librarian.writing.recommendations_writer.Agent") as MockAgent:
                MockAgent.return_value = MagicMock()

                from librarian.writing.recommendations_writer import RecommendationsWriter
                writer = RecommendationsWriter()

        from librarian.ranking.models import RankedCandidate, RankingResponse
        candidate = RankedCandidate(
            title="No DNA Book", author="Author", rank=1,
            confidence_score=70.0, reasoning="Limited info", dna=None
        )
        ranking = RankingResponse(candidates=[candidate], total_analyzed=1, failed_analyses=0)

        summaries = writer._build_candidate_summaries(ranking)
        assert "No DNA Book" in summaries
        assert "Analysis failed" in summaries
