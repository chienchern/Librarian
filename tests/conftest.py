"""Shared fixtures for the Librarian test suite."""

import sys
from pathlib import Path

import pytest

# Ensure src and tests are on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from helpers import make_book_dna, make_candidate_list, make_ranking_response, make_book_metadata


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_dna():
    return make_book_dna()


@pytest.fixture
def sample_candidate_list():
    return make_candidate_list()


@pytest.fixture
def sample_ranking():
    return make_ranking_response()


@pytest.fixture
def sample_metadata():
    return make_book_metadata()
