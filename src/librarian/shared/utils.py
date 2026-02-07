"""Shared utility functions for the Librarian application."""

from ..analysis.models import BookDNAResponse


def build_pillar_descriptions(dna: BookDNAResponse, selected_pillars: list[str]) -> list[str]:
    """
    Build formatted pillar descriptions for LLM prompts.

    Args:
        dna: Book DNA response containing pillar data
        selected_pillars: List of pillar names to include

    Returns:
        List of formatted pillar descriptions
    """
    pillar_descriptions = []
    for pillar_name in selected_pillars:
        pillar = getattr(dna, pillar_name)
        if pillar_name == "setting":
            desc = f"Setting: {pillar.full_text}"
        else:
            desc = f"{pillar_name.replace('_', ' ').title()}: {pillar.full_text}"
        pillar_descriptions.append(desc)

    return pillar_descriptions
