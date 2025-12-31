import logging
from pathlib import Path
from strands import Agent
from strands.types.exceptions import StructuredOutputException
from .models import ParsedBookQuery
from ..shared.ai.gemini_client import create_gemini_model

logger = logging.getLogger("librarian")


class QueryParser:
    """Uses LLM to parse ambiguous book search queries."""
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "query_parser_system.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        
        self.model = create_gemini_model(
            model_id="gemini-3-flash-preview",
            temperature=0.1,
            max_output_tokens=1024
        )
        self.agent = Agent(model=self.model, system_prompt=self.system_prompt)
    
    def parse(self, query: str) -> ParsedBookQuery:
        """Parse a user's search query into structured fields."""
        try:
            logger.info(f"Gemini query parser prompt: Parse this book search query: {query}", extra={'query': True})
            
            result = self.agent(
                f"Parse this book search query: {query}",
                structured_output_model=ParsedBookQuery
            )
            
            parsed = result.structured_output
            logger.info(f"Gemini parser response: title={parsed.title!r}, author={parsed.author!r}", extra={'response': True})
            
            return parsed
        except StructuredOutputException as e:
            logger.warning(f"Structured output failed: {e}")
            # Fall back to using query as title
            fallback = ParsedBookQuery(title=query)
            logger.info(f"Fallback to raw query: {fallback.title!r}", extra={'response': True})
            return fallback