from pydantic import BaseModel, Field
from ..analysis.models import BookDNAResponse


class RecommendationCard(BaseModel):
    """Enhanced recommendation with empathetic copy."""
    title: str = Field(description="Book title")
    author: str = Field(description="Book author")
    rank: int = Field(description="Rank position (1 = best match)")
    confidence_score: float = Field(description="0-100 confidence in the match")
    why_it_matches: str = Field(description="Empathetic explanation of how it matches user preferences")
    what_is_fresh: str = Field(description="What makes this a 'pivot' rather than a 'clone'")
    dna: BookDNAResponse | None = Field(description="DNA analysis (None if analysis failed)")


class LLMRecommendation(BaseModel):
    """LLM output format for a single recommendation (without DNA data)."""
    title: str = Field(description="Book title")
    author: str = Field(description="Book author")
    rank: int = Field(description="Rank position (1 = best match)")
    confidence_score: float = Field(description="0-100 confidence in the match")
    why_it_matches: str = Field(description="Empathetic explanation of how it matches user preferences")
    what_is_fresh: str = Field(description="What makes this a 'pivot' rather than a 'clone'")


class RecommendationOutput(BaseModel):
    """LLM output format for recommendation writing."""
    recommendations: list[LLMRecommendation] = Field(description="Enhanced recommendations with empathetic copy")


class RecommendationResponse(BaseModel):
    """Final response with enhanced recommendations."""
    recommendations: list[RecommendationCard] = Field(description="Enhanced recommendation cards")
    total_analyzed: int = Field(description="Number of candidates successfully analyzed")
    failed_analyses: int = Field(description="Number of candidate analyses that failed")