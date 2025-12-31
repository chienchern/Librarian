import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from exa_py import Exa
from strands.tools import tool
from ..shared.config.api_keys import get_exa_api_key

logger = logging.getLogger("librarian")


def _sync_exa_search(query: str, num_results: int = 3) -> str:
    """Synchronous Exa search for use in thread pool."""
    exa_api_key = get_exa_api_key()
    if not exa_api_key:
        return "Error: EXA_API_KEY not found in environment"
    
    try:
        exa = Exa(api_key=exa_api_key)
        
        # Search with include_domains for better book content
        results = exa.search(
            query,
            num_results=num_results,
            include_domains=["goodreads.com", "reddit.com", "bookish.com", "theguardian.com", "nytimes.com"]
        )
        
        logger.info(f"Exa found {len(results.results)} results for: {query[:50]}...", extra={'response': True})
        
        # Get content using URLs from search results
        if results.results:
            urls = [result.url for result in results.results]
            content_results = exa.get_contents(urls)
            
            # Combine all results into one text block with 5K char limit per source
            combined_content = []
            for i, result in enumerate(content_results.results):
                title = results.results[i].title if i < len(results.results) else "Unknown"
                if result.text:
                    # Limit content to 5K characters per source
                    truncated_text = result.text[:5000]
                    if len(result.text) > 5000:
                        truncated_text += "..."
                    
                    combined_content.append(f"Source: {title}\n{truncated_text}\n")
        else:
            combined_content = []
        
        content = "\n---\n".join(combined_content)
        return content if content else "No relevant content found for this query."
        
    except Exception as e:
        logger.error(f"Exa search failed for '{query}': {e}")
        return f"Error searching for book analysis: {e}"


@tool
async def search_book_analysis_parallel(queries: list[str], num_results: int = 3) -> str:
    """Search for book analysis using multiple parallel Exa queries.
    
    Args:
        queries: List of search queries to run in parallel
        num_results: Number of results to return per query (default 3)
    
    Returns:
        Combined text content from all search results
    """
    if not queries:
        return "No search queries provided"
    
    logger.info(f"Running {len(queries)} parallel Exa searches", extra={'query': True})
    
    # Run searches in parallel using thread pool
    with ThreadPoolExecutor(max_workers=3) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, _sync_exa_search, query, num_results)
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks)
    
    # Combine all results
    combined_content = []
    total_chars = 0
    
    for i, content in enumerate(results):
        if content and not content.startswith("Error"):
            combined_content.append(f"=== Search {i+1} Results ===\n{content}")
            total_chars += len(content)
    
    final_content = "\n\n".join(combined_content)
    logger.info(f"Parallel search completed: {total_chars} total characters", extra={'response': True})
    
    return final_content if final_content else "No relevant content found for this book."


@tool
def search_book_analysis(query: str, num_results: int = 3) -> str:
    """Search for book analysis, reviews, and thematic discussions using Exa.ai.
    
    Args:
        query: Search query for book analysis (e.g., "Project Hail Mary thematic analysis")
        num_results: Number of results to return (default 3)
    
    Returns:
        Combined text content from search results
    """
    exa_api_key = get_exa_api_key()
    if not exa_api_key:
        return "Error: EXA_API_KEY not found in environment"
    
    try:
        logger.info(f"Exa search query: {query!r}", extra={'query': True})
        
        exa = Exa(api_key=exa_api_key)
        
        # Search with include_domains for better book content
        results = exa.search(
            query,
            num_results=num_results,
            include_domains=["goodreads.com", "reddit.com", "bookish.com", "theguardian.com", "nytimes.com"]
        )
        
        logger.info(f"Exa found {len(results.results)} results", extra={'response': True})
        
        # Get content using URLs from search results
        if results.results:
            urls = [result.url for result in results.results]
            logger.info(f"Fetching content from URLs: {urls}", extra={'query': True})
            
            content_results = exa.get_contents(urls)
            
            # Combine all results into one text block with 5K char limit per source
            combined_content = []
            for i, result in enumerate(content_results.results):
                title = results.results[i].title if i < len(results.results) else "Unknown"
                if result.text:
                    # Limit content to 5K characters per source
                    truncated_text = result.text[:5000]
                    if len(result.text) > 5000:
                        truncated_text += "..."
                    
                    combined_content.append(f"Source: {title}\n{truncated_text}\n")
                    logger.info(f"Retrieved {len(truncated_text)} chars from: {title}", extra={'response': True})
        else:
            combined_content = []
        
        content = "\n---\n".join(combined_content)
        total_content_length = len(content)
        logger.info(f"Total combined content: {total_content_length} characters", extra={'response': True})
        
        return content if content else "No relevant content found for this book."
        
    except Exception as e:
        logger.error(f"Exa search failed: {e}")
        return f"Error searching for book analysis: {e}"