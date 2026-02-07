# Tech Stack

## Languages
- Python 3.11+

## Frameworks
- Agent framework - Strands Agents (with Gemini provider)
- Web framework - FastAPI
- Templating - Jinja2 (server-rendered HTML)
- Frontend - Vanilla JavaScript

## Key Libraries
- **pydantic** - Data validation and structured output models
- **httpx** - Async HTTP client for Google Books API
- **python-dotenv** - Environment variable management
- **colorama** - Colored logging output
- **langdetect** - Language detection for filtering non-English books

## External APIs
- **Google Books API** - Seed book metadata lookup
- **Google Gemini** - LLM powering all AI agents (2.5 Flash for main agents, 3 Flash Preview for QueryParser)
- **Exa.ai** - Neural web search for BookAnalyzer agent
- **Tavily** - Advanced web search for CandidatesFinder agent

## Development Tools
- **pytest** + **pytest-asyncio** - Testing framework
- **strands-agents-tools** - Strands community tools package (Exa, Tavily wrappers)
