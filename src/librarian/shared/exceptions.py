"""Custom exceptions for the Librarian application."""


class LibrarianError(Exception):
    """Base exception for all Librarian errors."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail or message
        super().__init__(self.message)


class BookNotFoundError(LibrarianError):
    """Raised when a book cannot be found."""

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book not found: {book_id}",
            detail=f"No book found with ID: {book_id}"
        )


class AnalysisFailedError(LibrarianError):
    """Raised when book DNA analysis fails."""

    def __init__(self, title: str, author: str | None = None):
        book_ref = f"'{title}' by {author}" if author else f"'{title}'"
        super().__init__(
            message="Book analysis failed",
            detail=f"Failed to analyze DNA for {book_ref}"
        )


class CandidateSearchFailedError(LibrarianError):
    """Raised when candidate search fails."""

    def __init__(self, reason: str | None = None):
        detail = f"Failed to find book candidates: {reason}" if reason else "Failed to find book candidates"
        super().__init__(
            message="Candidate search failed",
            detail=detail
        )
