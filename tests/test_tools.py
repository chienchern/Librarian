"""Tests for Exa and Tavily tool wrappers."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ---------------------------------------------------------------------------
# Tavily tool
# ---------------------------------------------------------------------------

class TestTavilyTool:
    def test_search_book_candidates_success(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("librarian.ranking.tavily_tool.TavilyClient") as MockClient:
                mock_client = MagicMock()
                mock_client.search.return_value = {
                    "answer": "Try these books.",
                    "results": [
                        {"title": "Book A", "url": "http://a.com", "content": "A great book about space."},
                        {"title": "Book B", "url": "http://b.com", "content": "A thriller novel."},
                    ],
                }
                MockClient.return_value = mock_client

                from librarian.ranking.tavily_tool import search_book_candidates
                # The @tool decorator wraps the function; call the underlying
                result = search_book_candidates._tool_func(query="books like Dune")

        assert "Book A" in result
        assert "Book B" in result
        assert "Try these books." in result

    def test_search_book_candidates_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            # Remove TAVILY_API_KEY
            import os
            os.environ.pop("TAVILY_API_KEY", None)

            from librarian.ranking.tavily_tool import search_book_candidates
            result = search_book_candidates._tool_func(query="test")

        assert "API key not configured" in result

    def test_search_book_candidates_api_error(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"}):
            with patch("librarian.ranking.tavily_tool.TavilyClient") as MockClient:
                mock_client = MagicMock()
                mock_client.search.side_effect = RuntimeError("API error")
                MockClient.return_value = mock_client

                from librarian.ranking.tavily_tool import search_book_candidates
                result = search_book_candidates._tool_func(query="fail")

        assert "Search failed" in result


# ---------------------------------------------------------------------------
# Exa tool - single search
# ---------------------------------------------------------------------------

class TestExaTool:
    def test_search_book_analysis_success(self):
        with patch.dict("os.environ", {"EXA_API_KEY": "fake-key"}):
            with patch("librarian.analysis.exa_tool.Exa") as MockExa:
                mock_exa = MagicMock()

                # Mock search results
                mock_result = MagicMock()
                mock_result.url = "http://review.com"
                mock_result.title = "Great Review"
                mock_exa.search.return_value = MagicMock(results=[mock_result])

                # Mock content results
                mock_content = MagicMock()
                mock_content.text = "This book has excellent prose style and deep themes."
                mock_exa.get_contents.return_value = MagicMock(results=[mock_content])

                MockExa.return_value = mock_exa

                from librarian.analysis.exa_tool import search_book_analysis
                result = search_book_analysis._tool_func(query="Project Hail Mary analysis")

        assert "Great Review" in result
        assert "prose style" in result

    def test_search_book_analysis_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("EXA_API_KEY", None)

            from librarian.analysis.exa_tool import search_book_analysis
            result = search_book_analysis._tool_func(query="test")

        assert "EXA_API_KEY not found" in result

    def test_search_book_analysis_no_results(self):
        with patch.dict("os.environ", {"EXA_API_KEY": "fake-key"}):
            with patch("librarian.analysis.exa_tool.Exa") as MockExa:
                mock_exa = MagicMock()
                mock_exa.search.return_value = MagicMock(results=[])
                MockExa.return_value = mock_exa

                from librarian.analysis.exa_tool import search_book_analysis
                result = search_book_analysis._tool_func(query="obscure book")

        assert "No relevant content found" in result

    def test_search_book_analysis_truncates_long_content(self):
        with patch.dict("os.environ", {"EXA_API_KEY": "fake-key"}):
            with patch("librarian.analysis.exa_tool.Exa") as MockExa:
                mock_exa = MagicMock()
                mock_result = MagicMock()
                mock_result.url = "http://review.com"
                mock_result.title = "Long Review"
                mock_exa.search.return_value = MagicMock(results=[mock_result])

                # Content over 5000 chars
                long_text = "x" * 6000
                mock_content = MagicMock()
                mock_content.text = long_text
                mock_exa.get_contents.return_value = MagicMock(results=[mock_content])

                MockExa.return_value = mock_exa

                from librarian.analysis.exa_tool import search_book_analysis
                result = search_book_analysis._tool_func(query="long review book")

        # Should be truncated to 5000 chars + "..."
        assert len(result) < 6000
        assert "..." in result


# ---------------------------------------------------------------------------
# Exa tool - parallel search
# ---------------------------------------------------------------------------

class TestExaParallelTool:
    @pytest.mark.asyncio
    async def test_parallel_search_empty_queries(self):
        from librarian.analysis.exa_tool import search_book_analysis_parallel
        result = await search_book_analysis_parallel._tool_func(queries=[])
        assert result == "No search queries provided"

    @pytest.mark.asyncio
    async def test_parallel_search_combines_results(self):
        with patch("librarian.analysis.exa_tool._sync_exa_search") as mock_search:
            mock_search.side_effect = [
                "Source: Review 1\nContent 1",
                "Source: Review 2\nContent 2",
                "Source: Review 3\nContent 3",
            ]

            from librarian.analysis.exa_tool import search_book_analysis_parallel
            result = await search_book_analysis_parallel._tool_func(
                queries=["q1", "q2", "q3"]
            )

        assert "Search 1" in result
        assert "Search 2" in result
        assert "Search 3" in result

    @pytest.mark.asyncio
    async def test_parallel_search_skips_errors(self):
        with patch("librarian.analysis.exa_tool._sync_exa_search") as mock_search:
            mock_search.side_effect = [
                "Source: Good\nContent",
                "Error: API failed",
                "Source: Also Good\nContent 2",
            ]

            from librarian.analysis.exa_tool import search_book_analysis_parallel
            result = await search_book_analysis_parallel._tool_func(
                queries=["q1", "q2", "q3"]
            )

        assert "Good" in result
        assert "Also Good" in result
        assert "API failed" not in result
