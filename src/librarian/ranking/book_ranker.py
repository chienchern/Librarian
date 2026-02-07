import logging
from pathlib import Path
from strands import Agent
from strands.types.exceptions import StructuredOutputException
from .models import RankingResponse, RankedCandidate, RankingOutput, CandidateList
from ..analysis.models import BookDNAResponse
from ..analysis.book_analyzer import BookAnalyzer
from ..shared.ai.gemini_client import create_gemini_model
from ..shared.utils import build_pillar_descriptions

logger = logging.getLogger("librarian")


class BookRanker:
    """Strands agent that ranks book candidates based on DNA analysis and user preferences."""
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "book_ranker_system.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def _load_task_prompt(self) -> str:
        """Load the task prompt template from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "book_ranker_task.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.task_prompt_template = self._load_task_prompt()
        
        self.model = create_gemini_model(
            model_id="gemini-2.5-flash",
            temperature=0.3,  # Lower temperature for consistent ranking
            max_output_tokens=16384
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=[]  # No tools needed for ranking
        )
        
        # Initialize BookAnalyzer for candidate analysis
        self.book_analyzer = BookAnalyzer()
    
    async def rank_candidates(
        self,
        seed_dna: BookDNAResponse,
        candidates: CandidateList,
        selected_pillars: list[str],
        dealbreakers: list[str]
    ) -> RankingResponse:
        """Rank book candidates based on DNA analysis and user preferences."""
        try:
            logger.info(f"BOOK RANKER: Ranking {len(candidates.candidates)} candidates", extra={'step': True})

            # Step 1: Analyze each candidate sequentially
            analyzed_candidates = []
            failed_count = 0
            total_candidates = len(candidates.candidates)

            for i, candidate in enumerate(candidates.candidates, 1):
                logger.info(f"Analyzing candidate {i}/{total_candidates}: '{candidate.title}' by {candidate.author}...", extra={'query': True})

                # Analyze candidate using BookAnalyzer (async)
                candidate_dna = await self.book_analyzer.analyze(
                    title=candidate.title,
                    author=candidate.author
                )

                if candidate_dna:
                    analyzed_candidates.append({
                        'candidate': candidate,
                        'dna': candidate_dna
                    })
                    logger.info(f"✓ Candidate {i}/{total_candidates} analysis completed: '{candidate.title}'", extra={'response': True})
                else:
                    failed_count += 1
                    logger.warning(f"✗ Candidate {i}/{total_candidates} analysis failed: '{candidate.title}' - skipping", extra={'response': True})

            if not analyzed_candidates:
                logger.error("All candidate analyses failed")
                return RankingResponse(
                    candidates=[],
                    total_analyzed=0,
                    failed_analyses=failed_count
                )

            # Step 2: Rank candidates using LLM
            logger.info(f"Ranking {len(analyzed_candidates)} analyzed candidates...", extra={'query': True})

            # Build pillar descriptions for ranking
            pillar_descriptions = build_pillar_descriptions(seed_dna, selected_pillars)

            # Create ranking prompt
            pillar_text = '\n'.join(f"- {desc}" for desc in pillar_descriptions)
            dealbreaker_text = ', '.join(dealbreakers) if dealbreakers else 'None'

            # Build candidate DNA summaries for LLM
            candidate_summaries = []
            for i, item in enumerate(analyzed_candidates, 1):
                candidate = item['candidate']
                dna = item['dna']
                summary = f"""
Candidate {i}: "{candidate.title}" by {candidate.author}
- Genre: {dna.genre}
- Setting: {dna.setting.full_text}
- Narrative Engine: {dna.narrative_engine.full_text}
- Prose Texture: {dna.prose_texture.full_text}
- Emotional Profile: {dna.emotional_profile.full_text}
- Structural Quirks: {dna.structural_quirks.full_text}
- Theme: {dna.theme.full_text}
- Dealbreakers: {', '.join(dna.dealbreakers)}
"""
                candidate_summaries.append(summary.strip())

            candidates_text = '\n\n'.join(candidate_summaries)

            prompt = self.task_prompt_template.format(
                seed_title=seed_dna.title,
                pillar_text=pillar_text,
                dealbreaker_text=dealbreaker_text,
                candidates_text=candidates_text,
                num_candidates=len(analyzed_candidates)
            )

            logger.info(f"Ranking prompt: {prompt}...", extra={'query': True})

            # Execute ranking (async)
            try:
                result = await self.agent.invoke_async(
                    prompt,
                    structured_output_model=RankingOutput
                )

                llm_ranking = result.structured_output
                logger.info(f"LLM ranking output: {len(llm_ranking.candidates)} candidates returned", extra={'response': True})

            except StructuredOutputException as e:
                logger.error(f"LLM failed to produce structured ranking output: {e}")
                logger.error(f"Prompt length: {len(prompt)} chars")
                logger.error(f"Number of candidates to rank: {len(analyzed_candidates)}")
                raise

            # Convert LLM output to full RankedCandidate objects with DNA
            ranked_candidates = []
            for llm_candidate in llm_ranking.candidates:
                # Find matching analyzed candidate to get DNA
                candidate_dna = None
                for item in analyzed_candidates:
                    if (item['candidate'].title == llm_candidate.title and
                        item['candidate'].author == llm_candidate.author):
                        candidate_dna = item['dna']
                        break

                ranked_candidate = RankedCandidate(
                    title=llm_candidate.title,
                    author=llm_candidate.author,
                    rank=llm_candidate.rank,
                    confidence_score=llm_candidate.confidence_score,
                    reasoning=llm_candidate.reasoning,
                    dna=candidate_dna
                )
                ranked_candidates.append(ranked_candidate)

            # Create final response
            ranking = RankingResponse(
                candidates=ranked_candidates,
                total_analyzed=len(analyzed_candidates),
                failed_analyses=failed_count
            )

            logger.info(f"✓ Ranking completed - {len(ranking.candidates)} candidates ranked", extra={'response': True})

            for candidate in ranking.candidates:
                logger.info(f"Rank {candidate.rank}: '{candidate.title}' (Score: {candidate.confidence_score})", extra={'response': True})
                logger.info(f"  Reasoning: {candidate.reasoning}", extra={'response': True})

            return ranking

        except StructuredOutputException as e:
            logger.error(f"Structured output failed for ranking: {e}")
            return RankingResponse(candidates=[], total_analyzed=0, failed_analyses=len(candidates.candidates))
        except Exception as e:
            logger.error(f"Ranking failed: {e}")
            return RankingResponse(candidates=[], total_analyzed=0, failed_analyses=len(candidates.candidates))