import logging
from pathlib import Path
from strands import Agent
from strands.types.exceptions import StructuredOutputException
from .models import BookDNAResponse
from .exa_tool import search_book_analysis, search_book_analysis_parallel
from ..shared.ai.gemini_client import create_gemini_model

logger = logging.getLogger("librarian")


class BookAnalyzer:
    """Strands agent that analyzes books using Exa.ai to extract DNA pillars."""
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "book_analyzer_system.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def _load_task_prompt(self) -> str:
        """Load the task prompt template from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "book_analyzer_task.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.task_prompt_template = self._load_task_prompt()
        
        self.model = create_gemini_model(
            model_id="gemini-2.5-flash",
            temperature=0.3,
            max_output_tokens=4096  # Increased from 2048 to handle nested structure
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=[search_book_analysis, search_book_analysis_parallel]
        )
    
    async def analyze(self, title: str, author: str, book_id: str = None) -> BookDNAResponse | None:
        """Analyze a book and extract its DNA pillars."""
        try:
            # Generate temp ID for candidates if no book_id provided
            analysis_id = book_id or f"candidate_{title.replace(' ', '_').lower()}"

            # Major step logging with progress indicators
            logger.info(f"BOOK DNA ANALYSIS: {title} by {author} (ID: {analysis_id})", extra={'step': True})
            logger.info("Step 1/3: Preparing analysis prompt...", extra={'query': True})

            prompt = self.task_prompt_template.format(title=title, author=author)
            logger.info(f"Agent prompt: {prompt}", extra={'query': True})

            logger.info("Step 2/3: Executing agent analysis (search + DNA extraction)...", extra={'query': True})

            result = await self.agent.invoke_async(
                prompt,
                structured_output_model=BookDNAResponse
            )

            logger.info("Step 3/3: Processing and validating results...", extra={'query': True})

            # Log the structured output
            dna = result.structured_output
            logger.info(f"✓ DNA analysis completed successfully", extra={'response': True})
            logger.info(f"DNA extracted - Genre: {dna.genre}", extra={'response': True})
            logger.info(f"DNA extracted - Setting: {dna.setting.summary} ({dna.setting.time}, {dna.setting.place})", extra={'response': True})
            logger.info(f"DNA extracted - Engine: {dna.narrative_engine.summary}, Theme: {dna.theme.summary}", extra={'response': True})

            # Ensure the response has the correct book_id and title
            dna.book_id = analysis_id
            dna.title = title

            logger.info(f"DNA analysis completed successfully", extra={'response': True})
            return dna

        except StructuredOutputException as e:
            logger.error(f"Structured output failed for {title}: {e}")
            return None
        except Exception as e:
            logger.error(f"Book analysis failed for {title}: {e}")
            return None