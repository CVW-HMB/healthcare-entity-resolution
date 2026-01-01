"""Canonicalization module for creating resolved physician entities."""

from .confidence import (
    calculate_all_confidences,
    calculate_entity_confidence,
    calculate_record_confidence,
)
from .ids import (
    assign_canonical_ids,
    get_canonical_id_stats,
)
from .merge import (
    merge_all_clusters,
    merge_cluster_attributes,
)

__all__ = [
    # ID assignment
    "assign_canonical_ids",
    "get_canonical_id_stats",
    # Confidence
    "calculate_entity_confidence",
    "calculate_record_confidence",
    "calculate_all_confidences",
    # Merging
    "merge_cluster_attributes",
    "merge_all_clusters",
]
