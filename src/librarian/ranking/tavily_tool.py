import logging
from strands import tool
from tavily import TavilyClient

from ..shared.config.api_keys import get_tavily_api_key

logger = logging.getLogger("librarian")


@tool
def search_book_candidates(query: str) -> str:
    """
    Search for book candidates using Tavily with advanced depth.
    
    Args:
        query: Search query for book recommendations
        
    Returns:
        Search results as formatted string
    """
    try:
        logger.info(f"QUERY: Tavily search query: {query!r}", extra={'query': True})
        
        # Get API key from environment
        api_key = get_tavily_api_key()
        if not api_key:
            logger.error("TAVILY_API_KEY environment variable not set")
            return "Search failed: API key not configured"
        
        # Create Tavily client and execute search
        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=True,
            include_raw_content=False
        )
        
        logger.info(f"RESPONSE: Tavily found {len(results.get('results', []))} results", extra={'response': True})
        
        # Log AI summary if available
        if results.get('answer'):
            summary_length = len(results['answer'])
            logger.info(f"RESPONSE: AI summary generated: {summary_length} chars", extra={'response': True})
        
        # Log individual results with character limits
        for i, result in enumerate(results.get('results', []), 1):
            content_length = len(result.get('content', ''))
            logger.info(f"RESPONSE: Retrieved result {i}: {result.get('title', 'No title')} ({content_length} chars)", extra={'response': True})
        
        # Format results for the LLM
        formatted_results = []
        
        # Add AI summary if available
        if results.get('answer'):
            formatted_results.append(f"AI Summary: {results['answer']}")
        
        # Add individual search results
        for i, result in enumerate(results.get('results', []), 1):
            formatted_result = f"""
Result {i}: {result.get('title', 'No title')}
URL: {result.get('url', 'No URL')}
Content: {result.get('content', 'No content')}
"""
            formatted_results.append(formatted_result.strip())
        
        return '\n\n'.join(formatted_results)
        
    except Exception as e:
        logger.error(f"Tavily search failed for query '{query}': {e}")
        return f"Search failed: {str(e)}"