from pydantic import BaseModel, Field
from typing import Literal


class DNAPillar(BaseModel):
    """Generic pillar with full text and summary."""
    full_text: str = Field(description="Complete pillar description")
    summary: str = Field(description="2-3 word summary for search")


class DNASettingPillar(BaseModel):
    """Setting pillar with time/place/vibe breakdown."""
    time: str = Field(description="Time period or era")
    place: str = Field(description="Geographic location or setting")
    vibe: str = Field(description="Atmospheric or sensory quality")
    full_text: str = Field(description="Complete setting description")
    summary: str = Field(description="2-3 word summary for search")


class BookDNA(BaseModel):
    """Complete DNA analysis of a book."""
    book_id: str
    title: str
    pillars: dict = Field(description="The 6 DNA pillars")
    dealbreakers: list[str] = Field(description="Polarizing tropes to avoid")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure pillars has the expected structure
        if "pillars" not in data:
            self.pillars = {
                "setting": {"time": "", "place": "", "vibe": ""},
                "narrative_engine": "",
                "prose_texture": "",
                "emotional_profile": "",
                "structural_quirks": "",
                "theme": ""
            }


class BookDNAResponse(BaseModel):
    """Response format for book DNA analysis."""
    book_id: str
    title: str
    genre: str = Field(description="Book genre (e.g., 'Hard sci-fi', 'Literary fiction')")
    
    setting: DNASettingPillar
    narrative_engine: DNAPillar
    prose_texture: DNAPillar
    emotional_profile: DNAPillar
    structural_quirks: DNAPillar
    theme: DNAPillar
    
    dealbreakers: list[str] = Field(description="4 common polarizing tropes")