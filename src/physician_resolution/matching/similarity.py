"""Pairwise similarity scoring between physician records."""

import jellyfish
from rapidfuzz import fuzz

from ..etl.geocoder import calculate_distance_miles
from ..logging import get_logger
from ..schemas.matches import SimilarityScores
from ..schemas.records import PhysicianRecord

logger = get_logger("matching.similarity")


def calculate_name_similarity(name1: str | None, name2: str | None) -> float:
    """
    Calculate name similarity using multiple metrics.

    Combines:
    - Jaro-Winkler: good for typos
    - Token sort ratio: good for reordering
    - Partial ratio: good for abbreviations
    """
    if not name1 or not name2:
        return 0.0

    name1 = name1.upper().strip()
    name2 = name2.upper().strip()

    # Exact match
    if name1 == name2:
        return 1.0

    # Jaro-Winkler similarity (0-1)
    jaro = jellyfish.jaro_winkler_similarity(name1, name2)

    # Token sort ratio (handles reordering like "John Smith" vs "Smith, John")
    token_sort = fuzz.token_sort_ratio(name1, name2) / 100.0

    # Partial ratio (handles abbreviations like "J Smith" vs "John Smith")
    partial = fuzz.partial_ratio(name1, name2) / 100.0

    # Weighted combination
    score = (jaro * 0.4) + (token_sort * 0.4) + (partial * 0.2)

    return min(score, 1.0)


def calculate_first_name_similarity(first1: str | None, first2: str | None) -> float:
    """Calculate first name similarity, handling initials."""
    if not first1 or not first2:
        return 0.5  # Unknown - neutral score

    f1 = first1.upper().strip()
    f2 = first2.upper().strip()

    # Exact match
    if f1 == f2:
        return 1.0

    # Initial match (J matches JOHN)
    if len(f1) == 1 and f2.startswith(f1):
        return 0.8
    if len(f2) == 1 and f1.startswith(f2):
        return 0.8

    # String similarity
    return jellyfish.jaro_winkler_similarity(f1, f2)


def calculate_last_name_similarity(last1: str | None, last2: str | None) -> float:
    """Calculate last name similarity."""
    if not last1 or not last2:
        return 0.0  # Last name is critical

    l1 = last1.upper().strip()
    l2 = last2.upper().strip()

    # Normalize: remove apostrophes, hyphens for comparison
    l1_norm = l1.replace("'", "").replace("-", "").replace(" ", "")
    l2_norm = l2.replace("'", "").replace("-", "").replace(" ", "")

    if l1_norm == l2_norm:
        return 1.0

    # Jaro-Winkler for typos
    return jellyfish.jaro_winkler_similarity(l1_norm, l2_norm)


def calculate_location_score(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
    state1: str | None = None,
    state2: str | None = None,
) -> float:
    """
    Calculate location similarity based on distance.

    Score:
    - Same location (< 0.5 miles): 1.0
    - Same city (< 10 miles): 0.8
    - Same metro (< 50 miles): 0.5
    - Same state: 0.3
    - Different state: 0.1
    """
    # Try distance-based scoring first
    distance = calculate_distance_miles(lat1, lon1, lat2, lon2)

    if distance is not None:
        if distance < 0.5:
            return 1.0
        elif distance < 10:
            return 0.8
        elif distance < 50:
            return 0.5
        elif distance < 100:
            return 0.3
        else:
            return 0.1

    # Fall back to state comparison
    if state1 and state2:
        if state1.upper() == state2.upper():
            return 0.3
        else:
            return 0.1

    # No location info
    return 0.2  # Neutral


def calculate_specialty_similarity(spec1: str | None, spec2: str | None) -> float | None:
    """
    Calculate specialty match score.

    Returns None if either specialty is missing.
    """
    if not spec1 or not spec2:
        return None

    s1 = spec1.upper().strip()
    s2 = spec2.upper().strip()

    # Exact match
    if s1 == s2:
        return 1.0

    # Common abbreviation mappings
    mappings = {
        "INTERNAL MEDICINE": ["INTERNAL MED", "INT MEDICINE", "IM"],
        "FAMILY MEDICINE": ["FAMILY MED", "FAMILY PRACTICE", "FP"],
        "CARDIOLOGY": ["CARDIOVASCULAR DISEASE", "CARDIOVASCULAR MED", "CV"],
        "ORTHOPEDIC SURGERY": ["ORTHOPAEDIC SURGERY", "ORTHOPEDICS", "ORTHO"],
        "GENERAL SURGERY": ["SURGERY", "GEN SURGERY"],
        "PEDIATRICS": ["PEDIATRIC MEDICINE", "PEDS"],
        "OBSTETRICS & GYNECOLOGY": ["OB/GYN", "OB-GYN", "OBSTETRICS AND GYNECOLOGY"],
        "GASTROENTEROLOGY": ["GI", "GASTRO", "GI MEDICINE"],
        "EMERGENCY MEDICINE": ["ER", "EMERGENCY MED", "EM"],
    }

    # Check if they map to the same canonical specialty
    def get_canonical(spec: str) -> str:
        for canonical, variants in mappings.items():
            if spec == canonical or spec in variants:
                return canonical
        return spec

    if get_canonical(s1) == get_canonical(s2):
        return 1.0

    # Fuzzy match
    similarity = fuzz.ratio(s1, s2) / 100.0
    if similarity > 0.8:
        return similarity

    # Different specialties
    return 0.0


def calculate_npi_match(npi1: str | None, npi2: str | None) -> float | None:
    """
    Calculate NPI match score.

    Returns:
    - 1.0 if NPIs match
    - 0.0 if NPIs conflict (both present but different)
    - None if either NPI is missing
    """
    if not npi1 or not npi2:
        return None

    # Clean NPIs
    n1 = npi1.strip()
    n2 = npi2.strip()

    # Skip malformed NPIs
    if len(n1) != 10 or len(n2) != 10:
        return None
    if not n1.isdigit() or not n2.isdigit():
        return None

    if n1 == n2:
        return 1.0
    else:
        return 0.0  # Conflict - definitely different people


def calculate_similarity(
    record1: PhysicianRecord,
    record2: PhysicianRecord,
) -> SimilarityScores:
    """
    Calculate overall similarity between two records.

    Returns SimilarityScores with component and overall scores.
    """
    # NPI comparison
    npi_match = calculate_npi_match(record1.npi, record2.npi)

    # Name similarity
    last_sim = calculate_last_name_similarity(record1.name_last, record2.name_last)
    first_sim = calculate_first_name_similarity(record1.name_first, record2.name_first)
    name_similarity = (last_sim * 0.6) + (first_sim * 0.4)

    # Location score
    location_score = calculate_location_score(
        record1.latitude,
        record1.longitude,
        record2.latitude,
        record2.longitude,
        record1.facility_state,
        record2.facility_state,
    )

    # Specialty match
    specialty_match = calculate_specialty_similarity(record1.specialty, record2.specialty)

    # Calculate overall score
    overall_score = _calculate_overall_score(
        npi_match=npi_match,
        name_similarity=name_similarity,
        location_score=location_score,
        specialty_match=specialty_match,
    )

    return SimilarityScores(
        npi_match=npi_match,
        name_similarity=name_similarity,
        specialty_match=specialty_match,
        location_score=location_score,
        overall_score=overall_score,
    )


def _calculate_overall_score(
    npi_match: float | None,
    name_similarity: float,
    location_score: float,
    specialty_match: float | None,
) -> float:
    """
    Calculate weighted overall similarity score.

    NPI match/conflict trumps everything else.
    """
    # NPI match = almost certain
    if npi_match == 1.0:
        return 0.95

    # NPI conflict = definitely different people
    if npi_match == 0.0:
        return 0.0

    # No NPI - weight other factors
    weights = {
        "name": 0.50,
        "location": 0.30,
        "specialty": 0.20,
    }

    score = name_similarity * weights["name"]
    score += location_score * weights["location"]

    if specialty_match is not None:
        score += specialty_match * weights["specialty"]
    else:
        # Redistribute specialty weight to name
        score += name_similarity * weights["specialty"]

    return min(score, 1.0)
