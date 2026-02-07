# Requirements Document

## Introduction

The Librarian is a vibe-based book discovery engine that helps readers find books based on the underlying qualities they loved, not just surface-level similarities.

## Glossary

- **Inarticulate_Searcher**: A reader who knows how they want to feel but lacks the literary vocabulary to describe it
- **Seed_Book**: A book the user already likes, used as a baseline for recommendations
- **DNA_Tile**: A visual element representing one aspect of a book's "DNA" (mood, prose style, theme, etc.)
- **Pillar**: A category of book DNA (e.g., Setting, Prose, Theme, Mood, Pace). The pillars are defined below.
- **Pivot**: Finding books that match some pillars while deliberately changing others
- **Dealbreaker**: A DNA element the user explicitly wants to avoid

## The 6 DNA Pillars

| Pillar | Definition | Priority |
| :--- | :--- | :--- |
| **1. Prose Texture** | The stylistic "feel" of the writing, including sentence structure, vocabulary, and voice (e.g., Sparse/Clinical, Lush/Poetic, Witty/Conversational). | Highest |
| **2. Emotional Profile** | The dominant emotional resonance or "afterglow" of the book (e.g., Melancholy, Hopeful/Optimistic, Tense/Paranoid, Cozy). | High |
| **3. Theme** | The central "Big Idea" or moral question at the heart of the work (e.g., The cost of progress, the nature of grief, the absurdity of war). | Medium-High |
| **4. Setting** | The "Time, Place, and Atmosphere." This includes the physical location, the era, and the sensory "vibe" (e.g., Gritty, Pastoral, High-Tech). | Medium |
| **5. Narrative Engine** | The primary driver of the story's momentum. Is it **Plot-driven** (external events), **Character-driven** (internal growth), or **Concept-led** (exploring a "What If?" premise)? | Medium-Low |
| **6. Structural Quirks** | The formal architecture of the storytelling (e.g., Non-linear timelines, epistolary/found documents, multiple POVs, footnotes). | Lowest |

## Requirements

### Requirement 1: Seed Book Identification

**User Story:** As an Inarticulate_Searcher, I want to search for a book I already like, so that the system has a baseline for my preferences.

#### Acceptance Criteria

1. WHEN a user enters a search string, THE System SHALL call a Books API to return metadata (Title, Author, Blurb)
2. WHEN the Books API returns results, THE System SHALL display matching books for user selection
3. WHEN a user selects a book, THE System SHALL store it as the Seed_Book for the session

### Requirement 2: DNA Analysis and Selection

**User Story:** As an Inarticulate_Searcher, I want to see my Seed_Book analyzed into DNA pillars and select 1-3 that represent the "vibe" I want to keep, so that I can guide the recommendation process.

#### Acceptance Criteria

1. WHEN a Seed_Book is selected, THE System SHALL use AI agents to analyze the book and extract DNA for all 6 pillars
2. WHEN DNA analysis completes, THE System SHALL display interactive DNA_Tiles with summaries and full descriptions
3. WHEN the user selects pillars, THE System SHALL enforce a 1-3 selection limit (minimum 1, maximum 3)
4. WHEN the user selects dealbreakers, THE System SHALL mark those elements to avoid in recommendations
5. THE System SHALL pass selected pillars to the AI agents for consideration during candidate discovery and ranking

### Requirement 3: AI-Powered Recommendation Pipeline

**User Story:** As an Inarticulate_Searcher, I want the system to use AI agents to find, analyze, rank, and present book recommendations that match my selected preferences while offering fresh discoveries.

#### Acceptance Criteria

1. WHEN the user requests recommendations, THE System SHALL use a Candidates Finder agent to search for similar books using web search and select the top 3 for analysis
2. WHEN candidates are found, THE System SHALL use a Book Ranker agent to analyze each candidate's DNA and rank them by fit using LLM-assigned 0-100 confidence scores
3. WHEN ranking completes, THE System SHALL use a Recommendations Writer agent to create empathetic copy explaining why each book matches and what makes it fresh
4. THE System SHALL instruct AI agents to avoid books that match selected dealbreakers
5. THE System SHALL present up to 3 final recommendations with confidence scores, match explanations, and freshness highlights
6. THE System SHALL make recommendations clickable to search for the book on Google

