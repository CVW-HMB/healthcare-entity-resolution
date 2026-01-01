"""Schema module - dataclasses for domain objects."""

from .clusters import ClusterQuality
from .entities import CanonicalPhysician
from .matches import MatchDecision, MatchResult, SimilarityScores
from .records import ParsedName, PhysicianRecord

__all__ = [
    "ParsedName",
    "PhysicianRecord",
    "SimilarityScores",
    "MatchDecision",
    "MatchResult",
    "ClusterQuality",
    "CanonicalPhysician",
]
