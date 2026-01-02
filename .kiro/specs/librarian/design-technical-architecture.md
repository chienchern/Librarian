# Technical Architecture Diagram

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'12px', 'fontFamily':'arial'}}}%%
graph TB
    subgraph arch[" "]
        subgraph "Frontend"
            UI[Web Interface]
        end
        
        subgraph "API Layer"
            API[FastAPI Backend]
            GB[Google Books API]
        end
        
        subgraph "AI Agents"
            BA[BookAnalyzer<br/>DNA Extraction]
            CF[CandidatesFinder<br/>Book Discovery]
            BR[BookRanker<br/>Analysis & Scoring]
            RW[RecommendationsWriter<br/>Empathetic Copy]
        end
        
        subgraph "External Services"
            EXA[Exa.ai<br/>Neural Search]
            TAV[Tavily<br/>Web Search]
            GEM[Gemini 2.5 Flash<br/>Language Model]
        end
        
        UI --> API
        API --> GB
        API --> BA
        API --> CF
        API --> BR
        API --> RW
        
        BA --> EXA
        CF --> TAV
        BR --> BA
        
        BA --> GEM
        CF --> GEM
        BR --> GEM
        RW --> GEM
    end
    
    style BA fill:#e1f5fe,stroke:#1976d2
    style CF fill:#e8f5e8,stroke:#388e3c
    style BR fill:#fff3e0,stroke:#f57c00
    style RW fill:#fce4ec,stroke:#c2185b
    style arch fill:#e9ecef,stroke:#adb5bd,stroke-width:2px
```

## Description

This diagram shows the technical architecture of the Librarian system:

### Frontend Layer
- **Web Interface**: Server-rendered HTML with Jinja2 templates and vanilla JavaScript

### API Layer  
- **FastAPI Backend**: Main application server handling all requests
- **Google Books API**: External service for seed book metadata

### AI Agents Layer
- **BookAnalyzer**: Extracts DNA pillars from books using web research
- **CandidatesFinder**: Discovers similar books based on user preferences  
- **BookRanker**: Analyzes and ranks candidate books with confidence scores
- **RecommendationsWriter**: Generates empathetic user-facing copy

### External Services Layer
- **Exa.ai**: Neural search engine for book analysis research
- **Tavily**: Advanced web search for candidate discovery
- **Gemini 2.5 Flash**: Language model powering all AI agents

### Data Flow
1. User interactions flow from Web Interface to FastAPI Backend
2. Backend orchestrates AI agents based on user requests
3. Each agent uses appropriate external services for their specialized tasks
4. All agents leverage Gemini 2.5 Flash for language understanding and generation