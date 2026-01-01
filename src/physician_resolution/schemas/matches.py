from dataclasses import dataclass
from enum import Enum


class MatchDecision(Enum):
    """Classification of a potential match."""

    MATCH = "match"
    NON_MATCH = "non_match"
    UNCERTAIN = "uncertain"


@dataclass
class SimilarityScores:
    """Similarity scores between two physician records."""

    npi_match: float | None = None  # 1.0 match, 0.0 mismatch, None missing
    name_similarity: float = 0.0  # 0.0 to 1.0
    specialty_match: float | None = None  # 1.0 match, 0.0 mismatch, None missing
    location_score: float = 0.0  # Based on distance
    overall_score: float = 0.0  # Weighted combination

    def to_dict(self) -> dict:
        return {
            "npi_match": self.npi_match,
            "name_similarity": self.name_similarity,
            "specialty_match": self.specialty_match,
            "location_score": self.location_score,
            "overall_score": self.overall_score,
        }


@dataclass
class MatchResult:
    """Result of comparing two records."""

    source_id_1: str
    source_id_2: str
    scores: SimilarityScores
    decision: MatchDecision
    confidence: float
    match_type: str  # "npi_exact", "name_location", "name_only", etc.
