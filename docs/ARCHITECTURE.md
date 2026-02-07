# The Librarian - Technical Architecture

## Table of Contents

1. [User Journey Flow](#1-user-journey-flow)
2. [Key Design Decisions](#2-key-design-decisions)
3. [System Overview](#3-system-overview)
4. [Component Architecture](#4-component-architecture)
5. [Data Models](#5-data-models)
6. [API Design](#6-api-design)
7. [Integration Points](#7-integration-points)
8. [Future Considerations](#8-future-considerations)

---

## 1. User Journey Flow

### Core Flow: Search → Analyze → Discover

1. **Search Phase**
   - User enters a book search query (natural language or structured)
   - LLM-powered query parser (`QueryParser`) converts ambiguous queries into structured title/author fields
   - Google Books API returns up to 10 results with metadata (title, author, blurb, thumbnail)
   - Results are filtered for English-only books with cover images and descriptions

2. **Analysis Phase**
   - User selects a book they loved
   - `BookAnalyzer` agent extracts the book's "DNA" using:
     - Exa.ai web search to gather critical analysis and reviews
     - Gemini 2.5 Flash LLM to synthesize DNA pillars
   - DNA consists of 6 pillars:
     - **Setting**: Time, place, vibe (e.g., "1970s, American Southwest, Dusty frontier melancholy")
     - **Narrative Engine**: What drives the story forward (e.g., "Quest-driven survival")
     - **Prose Texture**: Writing style qualities (e.g., "Sparse, clinical, emotionally detached")
     - **Emotional Profile**: Reader emotional experience (e.g., "Creeping dread, quiet existential unease")
     - **Structural Quirks**: Non-standard narrative choices (e.g., "Unreliable narrator")
     - **Theme**: Central ideas (e.g., "Isolation vs. community")
   - System also identifies 4 potential "dealbreakers" (polarizing tropes to avoid)

3. **Selection Phase**
   - User selects 1-3 DNA pillars that represent the "vibe" they want to preserve
   - User optionally selects dealbreakers to avoid
   - Frontend enforces selection limits and provides visual feedback

4. **Discovery Phase (3-Step Pipeline)**

   **Step 1: Find Candidates** (`CandidatesFinder`)
   - Creates broad Tavily search query: `'books similar to "[title]" recommendations'`
   - LLM intelligently filters search results based on selected pillars
   - Returns top 5 candidates with ranking explanations
   - Selects top 3 for detailed analysis

   **Step 2: Rank Candidates** (`BookRanker`)
   - Sequentially analyzes each candidate book's DNA using `BookAnalyzer`
   - LLM ranks candidates based on:
     - How well they match selected pillars
     - Absence of selected dealbreakers
     - Novelty/freshness factor (pivot vs. clone)
   - Returns ranked list with confidence scores and reasoning

   **Step 3: Write Recommendations** (`RecommendationsWriter`)
   - Transforms ranked candidates into empathetic, human-readable copy
   - For each recommendation:
     - **Why It Matches**: Explains how it preserves the selected pillars
     - **What Is Fresh**: Highlights what's different/novel
   - Returns HTML-ready recommendation cards

5. **Presentation Phase**
   - Frontend displays recommendations inline with smooth scrolling
   - User sees ranked recommendations with empathetic explanations
   - Can start a new search or refine selections

### Key User Experience Principles

- **Progressiveness**: Multi-step flow with clear progress indicators (30s-2min total)
- **Transparency**: Every step is logged and explained to the user
- **Fault Tolerance**: Failed analyses are logged but don't block the entire flow
- **Empathy**: Final copy speaks to emotional connection, not just feature matching

---

## 2. Key Design Decisions

### Architectural Patterns

**Agent-Oriented Architecture**
- **Rationale**: [PLACEHOLDER - likely chosen for modularity, LLM orchestration, and tool use]
- **Trade-offs**: Each agent (BookAnalyzer, CandidatesFinder, BookRanker, RecommendationsWriter) is a self-contained unit with its own system prompt and tools
- **Constraint**: All agents use Strands framework for consistency

**Server-Rendered HTML with Progressive Enhancement**
- **Rationale**: [PLACEHOLDER - likely for simplicity, SEO, or avoiding SPA complexity]
- **Trade-offs**: Uses Jinja2 templates for initial page loads, JavaScript for progressive enhancement (async API calls, DOM updates)
- **Constraint**: No frontend framework (React/Vue) - vanilla JS only

**Sequential vs. Parallel Processing**
- **Rationale**: [PLACEHOLDER - likely balancing cost, rate limits, and latency]
- **Pattern**: Candidate DNA analyses run sequentially (not in parallel) to avoid overwhelming the LLM API
- **Trade-off**: Slower overall flow (~1-2min) but more reliable and cheaper

### Technology Choices

**Gemini 2.5 Flash as Primary LLM**
- **Rationale**: [PLACEHOLDER - likely cost, speed, or Strands framework compatibility]
- **Configuration**: Temperature varies by agent (0.3 for analysis/ranking, 0.4 for writing)
- **Constraint**: All agents use Gemini, no model mixing

**Strands Agent Framework**
- **Rationale**: [PLACEHOLDER - likely for built-in tool use, structured output, and async support]
- **Benefits**: Automatic structured output parsing, tool orchestration, async execution
- **Constraint**: Tightly coupled to Google's ecosystem

**FastAPI as Web Framework**
- **Rationale**: [PLACEHOLDER - likely for async support, automatic API docs, Python ecosystem]
- **Benefits**: Native async/await, Pydantic validation, automatic OpenAPI schema
- **Constraint**: Requires ASGI server (uvicorn)

**No Database**
- **Rationale**: [PLACEHOLDER - app is stateless, all data comes from external APIs, no need to persist]
- **Trade-offs**: Cannot cache book DNA analyses (re-analyze on every request)
- **Constraint**: All state is ephemeral, passed through API requests

### Design Principles

**Vibe-Based Discovery > Collaborative Filtering**
- Core philosophy: Extract literary "DNA" to enable precise pivoting (share 1-3 pillars but offer freshness)
- Avoids "people who bought X also bought Y" sameness

**Transparency & Logging**
- Every agent logs its reasoning, search queries, and structured outputs
- Custom colored logging with step/query/response markers for debuggability

**Fail-Safe Degradation**
- If 1 candidate analysis fails, continue with remaining candidates
- If all fail, show clear error message
- Never silently fail

---

## 3. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│                         (app.py)                             │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌──────────┐
   │  Seed  │  │Analysis│  │ Ranking  │
   │ Module │  │ Module │  │  Module  │
   └────┬───┘  └────┬───┘  └────┬─────┘
        │           │            │
        │           │            │
        ▼           ▼            ▼
   ┌────────────────────────────────┐
   │    External APIs & Services     │
   ├─────────────────────────────────┤
   │ • Google Books API (metadata)   │
   │ • Gemini API (LLM)              │
   │ • Exa.ai (book analysis search) │
   │ • Tavily (candidate search)     │
   └─────────────────────────────────┘
```

### Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI (async ASGI)
- **Templating**: Jinja2
- **Agent Framework**: Strands (Google's LLM orchestration)
- **LLM**: Google Gemini 2.5 Flash
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic v2
- **Testing**: pytest (async mode)

### Key Components

| Component | Purpose | External Dependencies |
|-----------|---------|----------------------|
| `seed` | Book search & metadata retrieval | Google Books API |
| `analysis` | DNA extraction from books | Exa.ai, Gemini |
| `ranking` | Candidate finding & ranking | Tavily, Gemini |
| `writing` | Empathetic recommendation copy | Gemini |
| `shared` | Common models, utilities, config | — |

---

## 4. Component Architecture

### Module Structure

```
src/librarian/
├── app.py                    # FastAPI application, routes, error handlers
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html
│   ├── search.html
│   ├── dna_analysis.html
│   └── recommendations_partial.html
├── seed/                     # Book search and metadata
│   ├── books_api.py          # Google Books API client
│   ├── query_parser.py       # LLM-powered query parsing
│   └── models.py
├── analysis/                 # Book DNA extraction
│   ├── book_analyzer.py      # DNA extraction agent
│   ├── exa_tool.py           # Exa.ai search tool
│   ├── models.py             # BookDNA, DNAPillar models
│   └── prompts/
│       ├── book_analyzer_system.md
│       └── book_analyzer_task.md
├── ranking/                  # Candidate finding and ranking
│   ├── candidates_finder.py  # Find candidate books
│   ├── book_ranker.py        # Rank candidates with DNA analysis
│   ├── models.py             # RankedCandidate, RankingResponse
│   └── prompts/
│       ├── candidates_finder_system.md
│       ├── candidates_finder_task.md
│       ├── book_ranker_system.md
│       └── book_ranker_task.md
├── writing/                  # Recommendation writing
│   ├── recommendations_writer.py  # Empathetic copy generation
│   ├── models.py             # RecommendationCard, RecommendationResponse
│   └── prompts/
│       ├── recommendations_writer_system.md
│       ├── recommendations_writer_task.md
│       ├── candidate_summary_template.md
│       └── candidate_summary_failed_template.md
└── shared/                   # Shared utilities
    ├── models/
    │   ├── book_metadata.py  # BookMetadata model
    │   └── requests.py       # API request models
    ├── ai/
    │   ├── gemini_client.py  # Gemini model factory
    │   └── strands_exceptions.py
    ├── config/
    │   └── api_keys.py       # Environment variable loading
    ├── logging/
    │   └── colored_formatter.py  # Custom colored logging
    ├── exceptions.py         # Custom exception hierarchy
    └── utils.py              # Shared helper functions
```

### Component Interactions

#### Seed Module (`seed/`)
- **`BooksAPI`**: Google Books API client
  - `search(query)`: Returns list of `BookMetadata` objects
  - `get_book(book_id)`: Returns single `BookMetadata`
  - Uses `QueryParser` to convert natural language queries to structured searches
  - Filters results for English books with covers and descriptions
  - Deduplicates results by (title, author)

- **`QueryParser`**: LLM-powered query parser
  - Converts ambiguous queries like "dune" → structured `{title: "Dune", author: null}`
  - Uses Gemini 2.5 Flash with structured output
  - Falls back to raw query if parsing fails

#### Analysis Module (`analysis/`)
- **`BookAnalyzer`**: DNA extraction agent
  - `analyze(title, author, book_id)`: Returns `BookDNAResponse` or None
  - Uses Exa.ai to search for book reviews and analysis
  - LLM synthesizes DNA pillars from search results
  - Temperature: 0.3 (consistent analysis)
  - Max tokens: 4096

- **`exa_tool`**: Strands tools for Exa.ai search
  - `search_book_analysis(title, author)`: Single search
  - `search_book_analysis_parallel(title, author)`: Parallel searches

#### Ranking Module (`ranking/`)
- **`CandidatesFinder`**: Find candidate books
  - `find_candidates(seed_dna, selected_pillars, dealbreakers)`: Returns `CandidateList`
  - Uses Tavily to search for similar books
  - LLM filters results based on pillar descriptions
  - Returns top 5 candidates, selects top 3 for analysis
  - Temperature: 0.4 (diverse recommendations)

- **`BookRanker`**: Rank candidates with DNA analysis
  - `rank_candidates(seed_dna, candidates, selected_pillars, dealbreakers)`: Returns `RankingResponse`
  - Sequentially analyzes each candidate using injected `BookAnalyzer`
  - LLM ranks candidates based on pillar match and novelty
  - Temperature: 0.3 (consistent ranking)
  - Max tokens: 16384

#### Writing Module (`writing/`)
- **`RecommendationsWriter`**: Empathetic copy generation
  - `write_recommendations(seed_dna, ranking, selected_pillars, dealbreakers)`: Returns `RecommendationResponse`
  - Transforms ranked candidates into human-readable cards
  - For each: "Why It Matches" + "What Is Fresh"
  - Temperature: 0.4 (creative writing)
  - Max tokens: 8192

#### Shared Module (`shared/`)
- **`models/`**: Core Pydantic models
  - `BookMetadata`: Book info from Google Books
  - Request/response models for all API endpoints

- **`ai/`**: LLM utilities
  - `gemini_client.create_gemini_model()`: Factory for Gemini models
  - Configures API key, temperature, max tokens

- **`config/`**: Configuration management
  - `api_keys.py`: Loads API keys from environment

- **`logging/`**: Custom logging
  - Colored output with step/query/response markers
  - Extra fields: `{'step': True}`, `{'query': True}`, `{'response': True}`

- **`exceptions.py`**: Custom exceptions
  - `LibrarianError` (base)
  - `BookNotFoundError`, `AnalysisFailedError`, `CandidateSearchFailedError`

### Dependency Injection

**BookAnalyzer Injection into BookRanker**
- `BookRanker` accepts an optional `book_analyzer` parameter
- In `app.py`, shared `BookAnalyzer` instance is injected during lifespan startup
- This enables reuse of the same analyzer instance across ranking operations

---

## 5. Data Models

All data is in-memory, using Pydantic models for validation and serialization.

### Core Models

#### BookMetadata (seed/shared)
```python
class BookMetadata(BaseModel):
    book_id: str          # Google Books ID
    title: str
    author: str
    blurb: str | None
    thumbnail: str | None
```

#### Book DNA Models (analysis)
```python
class DNAPillar(BaseModel):
    full_text: str        # Complete description
    summary: str          # 2-3 word search-friendly summary

class DNASettingPillar(BaseModel):
    time: str             # Time period (e.g., "1970s")
    place: str            # Location (e.g., "American Southwest")
    vibe: str             # Atmosphere (e.g., "Dusty frontier melancholy")
    full_text: str
    summary: str

class BookDNAResponse(BaseModel):
    book_id: str
    title: str
    genre: str            # e.g., "Hard sci-fi"
    setting: DNASettingPillar
    narrative_engine: DNAPillar
    prose_texture: DNAPillar
    emotional_profile: DNAPillar
    structural_quirks: DNAPillar
    theme: DNAPillar
    dealbreakers: list[str]  # 4 polarizing tropes
```

#### Ranking Models (ranking)
```python
class CandidateBook(BaseModel):
    title: str
    author: str
    source_snippet: str   # Ranking explanation from CandidatesFinder

class CandidateList(BaseModel):
    candidates: list[CandidateBook]

class RankedCandidate(BaseModel):
    title: str
    author: str
    rank: int                      # 1-3
    confidence_score: float        # 0-100
    reasoning: str                 # Why this ranking
    dna: BookDNAResponse | None    # Full DNA analysis

class RankingResponse(BaseModel):
    candidates: list[RankedCandidate]
    total_analyzed: int
    failed_analyses: int
```

#### Writing Models (writing)
```python
class RecommendationCard(BaseModel):
    title: str
    author: str
    rank: int
    confidence_score: float
    why_it_matches: str           # Preserves selected pillars
    what_is_fresh: str            # Novel/different elements
    dna: BookDNAResponse | None

class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationCard]
    total_analyzed: int
    failed_analyses: int
```

### Data Flow

```
User Query (str)
    ↓
QueryParser → ParsedBookQuery
    ↓
Google Books API → list[BookMetadata]
    ↓
User selects book → BookMetadata
    ↓
BookAnalyzer → BookDNAResponse
    ↓
User selects pillars → (BookDNAResponse, selected_pillars, dealbreakers)
    ↓
CandidatesFinder → CandidateList
    ↓
BookRanker → RankingResponse (with embedded BookDNAResponse for each candidate)
    ↓
RecommendationsWriter → RecommendationResponse
    ↓
Frontend renders HTML
```

---

## 6. API Design

### RESTful JSON API

All API endpoints follow REST conventions with JSON request/response bodies.

#### Book Search Endpoints

**`GET /api/books/search?q={query}`**
- **Purpose**: Search for books
- **Query Params**: `q` (string, min_length=1)
- **Response**: `list[BookMetadata]`
- **Example**: `GET /api/books/search?q=dune`

**`GET /api/books/{book_id}`**
- **Purpose**: Get book metadata by ID
- **Path Params**: `book_id` (string, Google Books ID)
- **Response**: `BookMetadata | null`

#### Analysis Endpoint

**`GET /api/books/{book_id}/analyze`**
- **Purpose**: Analyze book and extract DNA
- **Path Params**: `book_id`
- **Response**: `BookDNAResponse`
- **Errors**:
  - 404: Book not found
  - 500: Analysis failed

#### Recommendation Pipeline Endpoints

**`POST /api/books/{book_id}/find-candidates`**
- **Purpose**: Find candidate books based on selected pillars
- **Request Body**:
  ```json
  {
    "selected_pillars": ["prose_texture", "theme"],
    "dealbreakers": ["love triangle"],
    "dna": { /* BookDNAResponse object */ }
  }
  ```
- **Response**: `CandidateList`
- **Validation**:
  - At least 1 pillar selected
  - Max 3 pillars
  - Valid pillar names

**`POST /api/books/{book_id}/rank-candidates`**
- **Purpose**: Rank candidates with DNA analysis
- **Request Body**:
  ```json
  {
    "candidates": [ /* list of CandidateBook */ ],
    "selected_pillars": ["prose_texture", "theme"],
    "dealbreakers": ["love triangle"],
    "seed_dna": { /* BookDNAResponse */ }
  }
  ```
- **Response**: `RankingResponse`

**`POST /api/books/{book_id}/write-recommendations`**
- **Purpose**: Generate empathetic recommendation copy
- **Request Body**:
  ```json
  {
    "ranking": { /* RankingResponse */ },
    "selected_pillars": ["prose_texture", "theme"],
    "dealbreakers": ["love triangle"],
    "seed_dna": { /* BookDNAResponse */ }
  }
  ```
- **Response**: `RecommendationResponse`

**`POST /api/books/{book_id}/recommendations-html`**
- **Purpose**: Get recommendations as rendered HTML (for HTMX-style updates)
- **Request Body**: Same as `/write-recommendations`
- **Response**: `HTMLResponse` (server-rendered partial)

### Web Page Endpoints

**`GET /`**
- **Purpose**: Home page with search box
- **Response**: `home.html` template

**`GET /search?q={query}`**
- **Purpose**: Book search results page
- **Response**: `search.html` template with book results

**`GET /book/{book_id}/analyze`**
- **Purpose**: DNA analysis page with pillar selection UI
- **Response**: `dna_analysis.html` template

### Error Handling

Global exception handler for custom errors:
- `BookNotFoundError` → 404
- `AnalysisFailedError` → 500
- `CandidateSearchFailedError` → 500
- All `LibrarianError` subclasses return JSON: `{"error": "...", "detail": "..."}`

---

## 7. Integration Points

### External APIs

#### Google Books API
- **Purpose**: Book search and metadata retrieval
- **Base URL**: `https://www.googleapis.com/books/v1/volumes`
- **Authentication**: API key (optional, but recommended)
- **Usage**:
  - `GET /volumes?q={query}`: Search books
  - `GET /volumes/{id}`: Get book details
- **Rate Limits**: [PLACEHOLDER - likely generous for free tier]
- **Filters Applied**:
  - `langRestrict=en`: English only
  - Custom: Must have cover image and description
- **Client**: httpx.AsyncClient (async)

#### Google Gemini API
- **Purpose**: LLM for all analysis, ranking, and writing tasks
- **Model**: `gemini-2.5-flash`
- **Authentication**: API key via Strands framework
- **Usage**:
  - Structured output parsing (Pydantic models)
  - Tool use (Exa, Tavily searches)
- **Configuration per Agent**:
  - BookAnalyzer: temp=0.3, max_tokens=4096
  - CandidatesFinder: temp=0.4, max_tokens=8192
  - BookRanker: temp=0.3, max_tokens=16384
  - RecommendationsWriter: temp=0.4, max_tokens=8192
- **Framework**: Strands (Google's official agent framework)

#### Exa.ai
- **Purpose**: High-quality web search for book analysis
- **Usage**: Find critical essays, reviews, and literary analysis
- **Integration**: Custom Strands tool (`exa_tool.py`)
- **Tools**:
  - `search_book_analysis(title, author)`: Single search
  - `search_book_analysis_parallel(title, author)`: Parallel searches
- **Authentication**: API key via `exa-py` library

#### Tavily API
- **Purpose**: Web search for candidate book discovery
- **Usage**: Find books similar to seed book
- **Integration**: Custom Strands tool (`tavily_tool.py` - not shown in files read, but referenced)
- **Authentication**: API key via `tavily-python` library
- **Query Pattern**: `'books similar to "{title}" recommendations'`

### Environment Variables

All API keys are loaded from `.env` file:
```
GOOGLE_BOOKS_API_KEY=...
GEMINI_API_KEY=...
EXA_API_KEY=...
TAVILY_API_KEY=...
```

Managed by `shared/config/api_keys.py` using `python-dotenv`.

---

## 8. Future Considerations

### Known Limitations

**No Caching**
- Every book analysis is fresh (no DNA persistence)
- Repeated analyses of popular books waste API calls
- **Future**: Add Redis or database caching for book DNA

**Sequential Candidate Analysis**
- BookRanker analyzes candidates one-by-one (1-2 min total)
- **Future**: Parallel analysis with rate limiting

**No User Accounts**
- Stateless app, no history or saved recommendations
- **Future**: User accounts, recommendation history, "liked" books

**Limited Error Recovery**
- If LLM produces malformed output, entire step fails
- **Future**: Retry logic, fallback strategies

### Planned Improvements

**Performance**
- Cache book DNA in database (PostgreSQL or Redis)
- Parallel candidate analysis with concurrency limits
- Consider cheaper/faster LLM for CandidatesFinder (e.g., Haiku)

**Features**
- User accounts and recommendation history
- "Vibe profiles" (save pillar preferences)
- Multi-book DNA blending (e.g., "Find books like A + B but without C")
- Export recommendations to Goodreads

**Reliability**
- Retry failed LLM calls with exponential backoff
- Graceful degradation for API outages
- Better structured output validation

**Infrastructure**
- Deployment to cloud (Vercel, Railway, or Render)
- Monitoring and observability (Sentry, Datadog)
- CI/CD pipeline for automated testing

### Technical Debt

**Prompt Management**
- Prompts are stored as `.md` files in `prompts/` subdirectories
- No versioning or A/B testing framework
- **Future**: Centralized prompt management with version control

**Type Safety**
- Some `| None` return types could be stricter
- **Future**: Use Result/Either pattern for clearer error handling

**Testing**
- Limited test coverage (tests exist but not comprehensive)
- **Future**: Comprehensive unit and integration tests
- Mock external APIs for faster CI

**Frontend**
- Vanilla JavaScript is hard to maintain as complexity grows
- **Future**: Consider HTMX or Alpine.js for reactivity without SPA complexity
