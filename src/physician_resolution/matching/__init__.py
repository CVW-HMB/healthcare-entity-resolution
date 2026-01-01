"""Matching module for physician entity resolution."""

from .blocking import (
    block_by_last_name_first_initial,
    block_by_last_name_state,
    block_by_npi,
    block_by_soundex_state,
    get_candidate_pairs,
)
from .classifier import (
    classify_match,
    find_matches,
    get_confirmed_matches,
)
from .similarity import (
    calculate_name_similarity,
    calculate_similarity,
)

__all__ = [
    # Blocking
    "block_by_npi",
    "block_by_last_name_state",
    "block_by_soundex_state",
    "block_by_last_name_first_initial",
    "get_candidate_pairs",
    # Similarity
    "calculate_similarity",
    "calculate_name_similarity",
    # Classification
    "classify_match",
    "find_matches",
    "get_confirmed_matches",
]
