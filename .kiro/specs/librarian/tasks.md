# Implementation Plan: The Librarian

## Overview

Iterative, user-centric implementation of the vibe-based book discovery engine. Each task delivers a complete vertical slice (backend + frontend) that can be tested end-to-end.

## Tasks

- [x] 1. Seed Metadata Gateway
  - **Backend:** Google Books API client + FastAPI endpoint (`/api/books/search`)
  - **Frontend:** Search box + results list (title, author, blurb) + book selection
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Agent - Book Analyzer
  - **Backend:** Strands agent using Exa.ai (neural search + content extraction) to generate BookDNA
  - **Frontend:** Display DNA Pillars as tiles after seed book selection
  - Used for both seed book analysis and candidate book analysis (batch mode)
  - _Requirements: 2.1_

- [x] 3. Agent - Book Candidates Finder
  - **Backend:** Strands agent using Tavily (advanced depth) with LLM filtering; selects top 3 candidates for analysis
  - **Frontend:** User selects Prioritize tiles and Dealbreakers before triggering search
  - Incorporate user's selections as search parameters and negative terms
  - _Requirements: 3.1, 3.2_

- [x] 4. Agent - Book Ranker
  - **Backend:** Strands agent that analyzes each candidate's DNA (via BookAnalyzer) and ranks them using LLM-assigned 0-100 confidence scores
  - **Frontend:** Display ranked candidates with scores and match explanations
  - LLM considers user-selected pillars and dealbreakers when scoring
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 5. Agent - Recommendations Writer
  - **Backend:** Strands agent to generate empathetic Match Card copy
  - **Frontend:** Display final recommendations with "Why It Matches" and "What Is Fresh" sections
  - _Requirements: 3.1_

- [x] 6. Orchestration Layer
  - **Backend:** Wire all agents together in the iterative pipeline:
    1. Seed Analysis (Book Analyzer)
    2. User Refinement HITL (display DNA, collect Prioritize/Dealbreakers)
    3. Candidate Discovery (Book Candidates Finder)
    4. Candidate Analysis (Book Analyzer in batch)
    5. Ranking & Writing (Book Ranker → Recommendations Writer)
  - **Frontend:** Complete flow from search → DNA selection → recommendations
  - _Requirements: 1.1, 2.1, 3.1_
