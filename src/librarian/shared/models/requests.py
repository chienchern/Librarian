"""Typed request models for API endpoints."""

from pydantic import BaseModel


class FindCandidatesRequest(BaseModel):
    """Request model for finding book candidates."""
    selected_pillars: list[str]
    dealbreakers: list[str] = []
    dna: dict | None = None


class RankCandidatesRequest(BaseModel):
    """Request model for ranking book candidates."""
    seed_dna: dict | None = None
    candidates: list | None = None
    selected_pillars: list[str]
    dealbreakers: list[str] = []


class WriteRecommendationsRequest(BaseModel):
    """Request model for writing recommendations."""
    seed_dna: dict | None = None
    ranking: dict | None = None
    selected_pillars: list[str]
    dealbreakers: list[str] = []


class RecommendationsHtmlRequest(BaseModel):
    """Request model for generating recommendations HTML."""
    recommendations: dict
