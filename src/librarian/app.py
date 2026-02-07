from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from .seed import BooksAPI
from .analysis import BookAnalyzer, BookDNAResponse
from .ranking import BookRanker, CandidatesFinder, CandidateList, RankingResponse
from .writing import RecommendationsWriter, RecommendationResponse
from .shared.models.book_metadata import BookMetadata
from .shared.models.requests import (
    FindCandidatesRequest,
    RankCandidatesRequest,
    WriteRecommendationsRequest,
    RecommendationsHtmlRequest,
)
from .shared.logging.colored_formatter import setup_logging
from .shared.exceptions import (
    LibrarianError,
    BookNotFoundError,
    AnalysisFailedError,
    CandidateSearchFailedError,
)

load_dotenv()

# Configure logging
setup_logging()
logger = logging.getLogger("librarian")

books_api: BooksAPI | None = None
book_analyzer: BookAnalyzer | None = None
candidates_finder: CandidatesFinder | None = None
book_ranker: BookRanker | None = None
recommendations_writer: RecommendationsWriter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global books_api, book_analyzer, candidates_finder, book_ranker, recommendations_writer
    books_api = BooksAPI()
    book_analyzer = BookAnalyzer()
    candidates_finder = CandidatesFinder()
    book_ranker = BookRanker(book_analyzer=book_analyzer)
    recommendations_writer = RecommendationsWriter()
    yield
    await books_api.close()


app = FastAPI(title="The Librarian", lifespan=lifespan)
templates = Jinja2Templates(directory="src/librarian/templates")


@app.exception_handler(LibrarianError)
async def librarian_error_handler(request: Request, exc: LibrarianError) -> JSONResponse:
    """Global exception handler for Librarian custom exceptions."""
    logger.error(f"LibrarianError: {exc.message} - {exc.detail}")

    # Map error types to HTTP status codes
    status_code = 500  # Default to internal server error
    if isinstance(exc, BookNotFoundError):
        status_code = 404
    elif isinstance(exc, AnalysisFailedError):
        status_code = 500
    elif isinstance(exc, CandidateSearchFailedError):
        status_code = 500

    return JSONResponse(
        status_code=status_code,
        content={"error": exc.message, "detail": exc.detail}
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with search box."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = Query(default="")):
    """Search results page."""
    books = []
    if q:
        logger.info(f"Web endpoint hit: /search?q={q!r}")
        books = await books_api.search(q)
        logger.info(f"Search completed, rendering {len(books)} results", extra={'response': True})
    return templates.TemplateResponse("search.html", {
        "request": request,
        "query": q,
        "books": books,
    })


@app.get("/book/{book_id}/analyze", response_class=HTMLResponse)
async def analyze_book_page(request: Request, book_id: str):
    """DNA analysis page for a selected book."""
    logger.info(f"Web endpoint hit: /book/{book_id}/analyze")
    
    # Get book metadata
    logger.info(f"Fetching book metadata for: {book_id}", extra={'query': True})
    book = await books_api.get_book(book_id)
    if not book:
        logger.error(f"Book not found: {book_id}")
        raise BookNotFoundError(book_id)

    logger.info(f"Book metadata retrieved: {book.title} by {book.author}", extra={'response': True})

    # Analyze the book
    dna = await book_analyzer.analyze(book.title, book.author, book_id)
    if not dna:
        logger.error(f"Analysis failed for: {book.title}")
        raise AnalysisFailedError(book.title, book.author)
    
    logger.info(f"Rendering DNA analysis page", extra={'response': True})
    return templates.TemplateResponse("dna_analysis.html", {
        "request": request,
        "book": book,
        "dna": dna,
    })


@app.get("/api/books/search")
async def api_search(q: str = Query(..., min_length=1)) -> list[BookMetadata]:
    """API endpoint for book search."""
    logger.info(f"API endpoint hit: /api/books/search?q={q!r}")
    return await books_api.search(q)


@app.get("/api/books/{book_id}")
async def api_get_book(book_id: str) -> BookMetadata | None:
    """API endpoint to get a specific book."""
    logger.info(f"API endpoint hit: /api/books/{book_id}")
    return await books_api.get_book(book_id)


@app.get("/api/books/{book_id}/analyze")
async def api_analyze_book(book_id: str) -> BookDNAResponse:
    """API endpoint to analyze a book and extract DNA pillars."""
    logger.info(f"API endpoint hit: /api/books/{book_id}/analyze")
    
    # First get the book metadata
    book = await books_api.get_book(book_id)
    if not book:
        raise BookNotFoundError(book_id)

    # Analyze the book
    dna = await book_analyzer.analyze(book.title, book.author, book_id)
    if not dna:
        raise AnalysisFailedError(book.title, book.author)
    
    return dna


@app.post("/api/books/{book_id}/find-candidates")
async def api_find_candidates(
    book_id: str,
    request: FindCandidatesRequest
) -> CandidateList:
    """API endpoint to find book candidates based on selected pillars and dealbreakers."""
    logger.info(f"API endpoint hit: /api/books/{book_id}/find-candidates")

    # Extract request data
    selected_pillars = request.selected_pillars
    selected_dealbreakers = request.dealbreakers
    dna_data = request.dna
    
    if not selected_pillars:
        raise HTTPException(status_code=400, detail="At least one pillar must be selected")
    
    if len(selected_pillars) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 pillars can be selected")
    
    if not dna_data:
        raise HTTPException(status_code=400, detail="DNA data is required")
    
    # Validate selected pillars exist in the DNA
    # Derive valid pillars from BookDNAResponse model (exclude metadata fields)
    excluded_fields = {"book_id", "title", "genre", "dealbreakers"}
    valid_pillars = [field for field in BookDNAResponse.model_fields.keys() if field not in excluded_fields]
    invalid_pillars = [p for p in selected_pillars if p not in valid_pillars]
    if invalid_pillars:
        raise HTTPException(status_code=400, detail=f"Invalid pillars: {invalid_pillars}")
    
    # Convert DNA data back to BookDNAResponse object
    try:
        dna = BookDNAResponse(**dna_data)
    except Exception as e:
        logger.error(f"Invalid DNA data: {e}")
        raise HTTPException(status_code=400, detail="Invalid DNA data format")
    
    # Find candidates using provided DNA (no re-analysis needed)
    candidates = await candidates_finder.find_candidates(dna, selected_pillars, selected_dealbreakers)
    if not candidates:
        raise CandidateSearchFailedError("LLM failed to produce candidates")

    if len(candidates.candidates) == 0:
        raise CandidateSearchFailedError("No candidates found. Try different pillar selections or fewer dealbreakers.")

    return candidates

@app.post("/api/books/{book_id}/rank-candidates")
async def api_rank_candidates(
    book_id: str,
    request: RankCandidatesRequest
) -> RankingResponse:
    """API endpoint to rank book candidates based on DNA analysis and user preferences."""
    logger.info(f"API endpoint hit: /api/books/{book_id}/rank-candidates")

    # Extract request data
    candidates_data = request.candidates
    selected_pillars = request.selected_pillars
    selected_dealbreakers = request.dealbreakers
    seed_dna_data = request.seed_dna
    
    if not candidates_data:
        raise HTTPException(status_code=400, detail="Candidates data is required")
    
    if not selected_pillars:
        raise HTTPException(status_code=400, detail="At least one pillar must be selected")
    
    if not seed_dna_data:
        raise HTTPException(status_code=400, detail="Seed DNA data is required")
    
    # Convert data back to objects
    try:
        candidates = CandidateList(candidates=candidates_data)
        seed_dna = BookDNAResponse(**seed_dna_data)
    except Exception as e:
        logger.error(f"Invalid request data: {e}")
        raise HTTPException(status_code=400, detail="Invalid request data format")
    
    # Rank candidates
    try:
        ranking = await book_ranker.rank_candidates(seed_dna, candidates, selected_pillars, selected_dealbreakers)
        
        if not ranking.candidates:
            raise HTTPException(status_code=404, detail="No candidates could be ranked. All analyses may have failed.")
        
        return ranking
        
    except Exception as e:
        logger.error(f"Ranking error: {e}")
        raise HTTPException(status_code=500, detail="Ranking failed - please try again")

@app.post("/api/books/{book_id}/write-recommendations")
async def api_write_recommendations(
    book_id: str,
    request: WriteRecommendationsRequest
) -> RecommendationResponse:
    """API endpoint to transform ranked candidates into empathetic recommendation copy."""
    logger.info(f"API endpoint hit: /api/books/{book_id}/write-recommendations")

    # Extract request data
    ranking_data = request.ranking
    selected_pillars = request.selected_pillars
    selected_dealbreakers = request.dealbreakers
    seed_dna_data = request.seed_dna
    
    if not ranking_data:
        raise HTTPException(status_code=400, detail="Ranking data is required")
    
    if not selected_pillars:
        raise HTTPException(status_code=400, detail="At least one pillar must be selected")
    
    if not seed_dna_data:
        raise HTTPException(status_code=400, detail="Seed DNA data is required")
    
    # Convert data back to objects
    try:
        ranking = RankingResponse(**ranking_data)
        seed_dna = BookDNAResponse(**seed_dna_data)
    except Exception as e:
        logger.error(f"Invalid request data: {e}")
        raise HTTPException(status_code=400, detail="Invalid request data format")
    
    # Write empathetic recommendations
    try:
        recommendations = await recommendations_writer.write_recommendations(
            seed_dna, ranking, selected_pillars, selected_dealbreakers
        )
        
        if not recommendations.recommendations:
            raise HTTPException(status_code=404, detail="No recommendations could be written.")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Recommendations writing error: {e}")
        raise HTTPException(status_code=500, detail="Recommendations writing failed - please try again")


@app.post("/api/books/{book_id}/recommendations-html", response_class=HTMLResponse)
async def api_recommendations_html(
    request: Request,
    book_id: str,
    request_data: WriteRecommendationsRequest
) -> HTMLResponse:
    """API endpoint to get recommendations as rendered HTML."""
    logger.info(f"API endpoint hit: /api/books/{book_id}/recommendations-html")
    
    # Use the existing write_recommendations logic
    try:
        recommendations = await api_write_recommendations(book_id, request_data)
        
        # Render the partial template
        html_content = templates.TemplateResponse(
            "recommendations_partial.html", 
            {"request": request, "recommendations": recommendations}
        ).body.decode('utf-8')
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HTML recommendations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations HTML")