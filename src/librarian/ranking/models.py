from pydantic import BaseModel, Field
from ..analysis.models import BookDNAResponse


# Candidate Finding Models
class CandidateBook(BaseModel):
    """A candidate book recommendation."""
    title: str = Field(description="Book title")
    author: str = Field(description="Book author")
    source_snippet: str = Field(description="Evidence snippet explaining why this is a match")


class CandidateList(BaseModel):
    """List of candidate book recommendations."""
    candidates: list[CandidateBook] = Field(description="List of candidate books")


# Ranking Models
class RankedCandidateOutput(BaseModel):
    """LLM output format for a single ranked candidate."""
    title: str = Field(description="Book title")
    author: str = Field(description="Book author") 
    rank: int = Field(description="Rank position (1 = best match)")
    confidence_score: float = Field(description="0-100 confidence in the match")
    reasoning: str = Field(description="Why this book matches the user's preferences")


class RankingOutput(BaseModel):
    """LLM output format for ranking candidates."""
    candidates: list[RankedCandidateOutput] = Field(description="Ranked candidate books")


class RankedCandidate(BaseModel):
    """A ranked candidate book with analysis and scoring."""
    title: str = Field(description="Book title")
    author: str = Field(description="Book author")
    rank: int = Field(description="Rank position (1 = best match)")
    confidence_score: float = Field(description="0-100 confidence in the match")
    reasoning: str = Field(description="Why this book matches the user's preferences")
    dna: BookDNAResponse | None = Field(description="DNA analysis (None if analysis failed)")


class RankingResponse(BaseModel):
    """Response containing ranked book recommendations."""
    candidates: list[RankedCandidate] = Field(description="Ranked candidate books")
    total_analyzed: int = Field(description="Number of candidates successfully analyzed")
    failed_analyses: int = Field(description="Number of candidate analyses that failed")