"""Typed request models for API endpoints."""

from pydantic import BaseModel


class FindCandidatesRequest(BaseModel):
    """Request model for finding book candidates."""
    selected_pillars: list[str]
    dealbreakers: list[str]
    dna: dict


class RankCandidatesRequest(BaseModel):
    """Request model for ranking book candidates."""
    seed_dna: dict
    candidates: dict
    selected_pillars: list[str]
    dealbreakers: list[str]


class WriteRecommendationsRequest(BaseModel):
    """Request model for writing recommendations."""
    seed_dna: dict
    ranking: dict
    selected_pillars: list[str]
    dealbreakers: list[str]


class RecommendationsHtmlRequest(BaseModel):
    """Request model for generating recommendations HTML."""
    recommendations: dict
