import logging
from pathlib import Path
from strands import Agent
from strands.types.exceptions import StructuredOutputException
from .models import RecommendationResponse, RecommendationCard, RecommendationOutput, LLMRecommendation
from ..ranking.models import RankingResponse
from ..analysis.models import BookDNAResponse
from ..shared.ai.gemini_client import create_gemini_model

logger = logging.getLogger("librarian")


class RecommendationsWriter:
    """Strands agent that transforms ranked candidates into empathetic recommendation copy."""
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "recommendations_writer_system.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def _load_task_prompt(self) -> str:
        """Load the task prompt template from external file."""
        prompt_path = Path(__file__).parent / "prompts" / "recommendations_writer_task.md"
        return prompt_path.read_text(encoding='utf-8').strip()
    
    def _load_candidate_summary_template(self) -> str:
        """Load the candidate summary template from external file."""
        template_path = Path(__file__).parent / "prompts" / "candidate_summary_template.md"
        return template_path.read_text(encoding='utf-8').strip()
    
    def _load_candidate_summary_failed_template(self) -> str:
        """Load the failed candidate summary template from external file."""
        template_path = Path(__file__).parent / "prompts" / "candidate_summary_failed_template.md"
        return template_path.read_text(encoding='utf-8').strip()
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.task_prompt_template = self._load_task_prompt()
        self.candidate_summary_template = self._load_candidate_summary_template()
        self.candidate_summary_failed_template = self._load_candidate_summary_failed_template()
        
        self.model = create_gemini_model(
            model_id="gemini-2.5-flash",
            temperature=0.4,  # Higher temperature for creative, empathetic writing
            max_output_tokens=8192
        )
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=[]  # No tools needed for writing
        )
    
    def _build_candidate_summaries(self, ranking: RankingResponse) -> str:
        """Build candidate DNA summaries for empathetic writing."""
        candidate_summaries = []
        for candidate in ranking.candidates:
            if candidate.dna:
                summary = self.candidate_summary_template.format(
                    rank=candidate.rank,
                    title=candidate.title,
                    author=candidate.author,
                    confidence_score=candidate.confidence_score,
                    reasoning=candidate.reasoning,
                    genre=candidate.dna.genre,
                    setting=candidate.dna.setting.full_text,
                    narrative_engine=candidate.dna.narrative_engine.full_text,
                    prose_texture=candidate.dna.prose_texture.full_text,
                    emotional_profile=candidate.dna.emotional_profile.full_text,
                    structural_quirks=candidate.dna.structural_quirks.full_text,
                    theme=candidate.dna.theme.full_text,
                    dealbreakers=', '.join(candidate.dna.dealbreakers)
                )
            else:
                summary = self.candidate_summary_failed_template.format(
                    rank=candidate.rank,
                    title=candidate.title,
                    author=candidate.author,
                    confidence_score=candidate.confidence_score,
                    reasoning=candidate.reasoning
                )
            
            candidate_summaries.append(summary.strip())
        
        return '\n\n'.join(candidate_summaries)
    
    def write_recommendations(
        self,
        seed_dna: BookDNAResponse,
        ranking: RankingResponse,
        selected_pillars: list[str],
        dealbreakers: list[str]
    ) -> RecommendationResponse:
        """Transform ranked candidates into empathetic recommendation copy."""
        try:
            logger.info(f"RECOMMENDATIONS WRITER: Creating empathetic copy for {len(ranking.candidates)} recommendations", extra={'step': True})
            
            if not ranking.candidates:
                logger.warning("No candidates to write recommendations for")
                return RecommendationResponse(
                    recommendations=[],
                    total_analyzed=ranking.total_analyzed,
                    failed_analyses=ranking.failed_analyses
                )
            
            # Build context for the LLM
            pillar_descriptions = []
            for pillar_name in selected_pillars:
                pillar = getattr(seed_dna, pillar_name)
                if pillar_name == "setting":
                    desc = f"Setting: {pillar.full_text}"
                else:
                    desc = f"{pillar_name.replace('_', ' ').title()}: {pillar.full_text}"
                pillar_descriptions.append(desc)
            
            pillar_text = '\n'.join(f"- {desc}" for desc in pillar_descriptions)
            dealbreaker_text = ', '.join(dealbreakers) if dealbreakers else 'None'
            
            # Build candidate summaries for empathetic writing
            candidates_text = self._build_candidate_summaries(ranking)
            
            # Create empathetic writing prompt
            prompt = self.task_prompt_template.format(
                seed_title=seed_dna.title,
                seed_author=getattr(seed_dna, 'author', 'Unknown'),
                pillar_text=pillar_text,
                dealbreaker_text=dealbreaker_text,
                candidates_text=candidates_text
            )
            
            logger.info(f"Writing empathetic recommendations...", extra={'query': True})
            logger.info(f"Prompt: {prompt}...", extra={'query': True})
            
            # Execute empathetic writing
            result = self.agent(
                prompt,
                structured_output_model=RecommendationOutput
            )
            
            llm_output = result.structured_output
            logger.info(f"✓ Empathetic copy generated for {len(llm_output.recommendations)} recommendations", extra={'response': True})
            
            # Convert to final response format
            recommendations = [
                RecommendationCard(
                    title=rec.title,
                    author=rec.author,
                    rank=rec.rank,
                    confidence_score=rec.confidence_score,
                    why_it_matches=rec.why_it_matches,
                    what_is_fresh=rec.what_is_fresh,
                    dna=None  # Not needed by frontend
                )
                for rec in llm_output.recommendations
            ]
            
            # Create final response
            response = RecommendationResponse(
                recommendations=recommendations,
                total_analyzed=ranking.total_analyzed,
                failed_analyses=ranking.failed_analyses
            )
            
            # Log the empathetic copy
            for rec in response.recommendations:
                logger.info(f"Recommendation {rec.rank}: '{rec.title}' by {rec.author}", extra={'response': True})
                logger.info(f"  Why It Matches: {rec.why_it_matches[:100]}...", extra={'response': True})
                logger.info(f"  What Is Fresh: {rec.what_is_fresh[:100]}...", extra={'response': True})
            
            logger.info(f"Recommendations writing completed successfully", extra={'response': True})
            return response
            
        except StructuredOutputException as e:
            logger.error(f"Structured output failed for recommendations writing: {e}")
            return RecommendationResponse(
                recommendations=[],
                total_analyzed=ranking.total_analyzed,
                failed_analyses=ranking.failed_analyses
            )
        except Exception as e:
            logger.error(f"Recommendations writing failed: {e}")
            return RecommendationResponse(
                recommendations=[],
                total_analyzed=ranking.total_analyzed,
                failed_analyses=ranking.failed_analyses
            )