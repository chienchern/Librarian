import logging
from pathlib import Path
from strands import Agent
from strands.types.exceptions import StructuredOutputException
from .models import CandidateList, CandidateBook
from ..analysis.models import BookDNAResponse
from .tavily_tool import search_book_candidates
from ..shared.ai.gemini_client import create_gemini_model

logger = logging.getLogger("librarian")


class CandidatesFinder:
    """Strands agent that finds book candidates using Tavily based on user-selected DNA pillars."""
    
    # Pillar priority for tie-breaking (higher number = higher priority)
    PILLAR_PRIORITY = {
        "prose_texture": 6,      # Highest priority
        "emotional_profile": 5,
        "theme": 4,
        "setting": 3,
        "narrative_engine": 2,
        "structural_quirks": 1   # Lowest priority
    }
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "candidates_finder_system.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def _load_task_prompt(self) -> str:
        """Load the task prompt template from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "candidates_finder_task.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.task_prompt_template = self._load_task_prompt()
        
        self.model = create_gemini_model(
            model_id="gemini-2.5-flash",
            temperature=0.4,  # Slightly higher for more diverse recommendations
            max_output_tokens=8192  # Increased from 3072 to handle longer structured output
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=[search_book_candidates]
        )
    
    def find_candidates(
        self, 
        seed_book_dna: BookDNAResponse, 
        selected_pillars: list[str], 
        dealbreakers: list[str]
    ) -> CandidateList | None:
        """Find book candidates based on user-selected pillars and dealbreakers."""
        try:
            # Major step logging
            logger.info(f"BOOK CANDIDATES FINDER: {seed_book_dna.title}", extra={'step': True})
            logger.info(f"Selected pillars: {selected_pillars}", extra={'query': True})
            logger.info(f"Selected dealbreakers: {dealbreakers}", extra={'query': True})
            
            # Build pillar descriptions for LLM filtering
            pillar_descriptions = []
            for pillar_name in selected_pillars:
                pillar = getattr(seed_book_dna, pillar_name)
                if pillar_name == "setting":
                    desc = f"Setting: {pillar.full_text}"
                else:
                    desc = f"{pillar_name.replace('_', ' ').title()}: {pillar.full_text}"
                pillar_descriptions.append(desc)
            
            logger.info(f"Pillar descriptions for filtering: {pillar_descriptions}", extra={'query': True})
            
            # Create single broad search query
            query = f'books similar to "{seed_book_dna.title}" recommendations'
            logger.info(f"Tavily search query: {query}", extra={'query': True})
            
            # Create the prompt for LLM to filter results
            pillar_text = '\n'.join(f"- {desc}" for desc in pillar_descriptions)
            dealbreaker_text = ', '.join(dealbreakers) if dealbreakers else 'None'
            
            prompt = self.task_prompt_template.format(
                query=query,
                pillar_text=pillar_text,
                dealbreaker_text=dealbreaker_text,
                seed_title=seed_book_dna.title
            )
            
            logger.info(f"LLM filtering prompt: {prompt}...", extra={'query': True})
            
            # Execute single LLM call with broad search + intelligent filtering
            result = self.agent(
                prompt,
                structured_output_model=CandidateList
            )
            
            # Log the results
            candidates = result.structured_output
            logger.info(f"LLM found {len(candidates.candidates)} candidates with ranking explanations", extra={'response': True})
            
            # Log all 5 candidates with their ranking explanations
            for i, candidate in enumerate(candidates.candidates, 1):
                logger.info(f"Rank {i}: '{candidate.title}' by {candidate.author}", extra={'response': True})
                logger.info(f"  Ranking explanation: {candidate.source_snippet}", extra={'response': True})
            
            # Select top 3 candidates for analysis
            top_candidates = CandidateList(candidates=candidates.candidates[:3])
            logger.info(f"Selected top 3 candidates for DNA analysis", extra={'response': True})
            
            for i, candidate in enumerate(top_candidates.candidates, 1):
                logger.info(f"Analyzing: Rank {i} - '{candidate.title}' by {candidate.author}", extra={'response': True})
            
            # Return top 3 candidates for analysis
            logger.info(f"Candidates finding completed successfully", extra={'response': True})
            return top_candidates
            
        except StructuredOutputException as e:
            logger.error(f"Structured output failed for candidates: {e}")
            return None
        except Exception as e:
            logger.error(f"Candidates finding failed: {e}")
            return None