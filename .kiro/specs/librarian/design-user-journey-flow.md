# User Journey Flow Diagram

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'12px', 'fontFamily':'arial', 'lineColor':'#333333', 'primaryTextColor':'#333333'}}}%%
flowchart TD
    subgraph journey[" "]
        A["Search for a book you love
                <small><i>
                    - Google Books API
                </i></small>"] 
        --> B[Select your seed book]
        B --> C["Review the book's DNA analysis
                <small><i>
                    - BookAnalyzer Agent
                    - Exa.ai web search
                </i></small>"]
        C --> D[Choose 1-3 pillars that matter to you]
        D --> E[Mark any dealbreakers to avoid]
        E --> F["Get personalized recommendations 
                <small><i>
                    - CandidatesFinder + Tavily
                    - BookRanker (using BookAnalyzer on candidates)
                    - RecommendationsWriter
                </i></small>"]
    end
    
    style A fill:#f8f9fa,stroke:#6c757d,color:#333333
    style B fill:#f8f9fa,stroke:#6c757d,color:#333333
    style C fill:#e3f2fd,stroke:#1976d2,color:#333333
    style D fill:#f8f9fa,stroke:#6c757d,color:#333333
    style E fill:#f8f9fa,stroke:#6c757d,color:#333333
    style F fill:#e8f5e8,stroke:#388e3c,color:#333333
    style journey fill:#e9ecef,stroke:#adb5bd,stroke-width:2px
```

## Description

This diagram shows the complete user journey through the Librarian system:

1. **Search Phase**: User searches for a book they love using Google Books API
2. **Selection Phase**: User selects their seed book from search results
3. **Analysis Phase**: BookAnalyzer agent extracts the book's DNA using Exa.ai web search
4. **Preference Phase**: User chooses 1-3 DNA pillars that matter most to them
5. **Filtering Phase**: User marks any dealbreakers to avoid in recommendations
6. **Recommendation Phase**: Multi-agent pipeline generates personalized recommendations using CandidatesFinder, BookRanker, and RecommendationsWriter agents